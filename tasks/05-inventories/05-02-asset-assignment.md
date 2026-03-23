# 05-02 자산 배정 및 반납

## 1. 개요

등록된 자산을 개인 또는 부서에 배정하고, 반납/이동을 처리하는 기능을 제공한다. 입사자/퇴사자 체크리스트를 통해 자산 배정 및 회수 프로세스를 표준화하며, 모든 배정/반납 이력은 자산 이력(`asset_history`)에 자동으로 기록된다.

- **모듈**: 자산관리 (Inventories)
- **의존성**: `05-01` 자산 등록 및 분류, `01-02` 사용자 관리, `01-03` 조직도
- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)

---

## 2. 기능 요구사항

### 2.1 자산 배정

#### 2.1.1 개인 배정

- 특정 사용자에게 자산을 배정한다.
- 배정 시 `assignee_type`은 `USER`, `assignee_id`는 사용자 UUID이다.
- 배정 가능 조건: 자산 상태가 `AVAILABLE`인 경우에만 가능
- 배정 시 자산 상태를 `IN_USE`로 자동 변경한다.
- 동일 자산을 중복 배정할 수 없다 (이미 `is_active = true`인 배정이 있으면 불가).

#### 2.1.2 부서 배정

- 공용 자산으로 부서에 배정한다.
- 배정 시 `assignee_type`은 `DEPARTMENT`, `assignee_id`는 부서 UUID이다.
- 회의실 장비, 공용 프린터 등 부서 공용 자산에 사용한다.

#### 2.1.3 배정 확인서

- 자산을 배정받은 사용자는 배정 확인(수령 확인)을 처리한다.
- 확인 시 `confirmed_at` 시각이 기록된다.
- 미확인 배정 목록을 관리자가 조회할 수 있다.

### 2.2 자산 반납

- 배정된 자산을 반납 처리한다.
- 반납 시 자산 상태를 `AVAILABLE`로 자동 변경한다.
- 반납 시 반납 상태 점검을 수행한다:
  - `GOOD` (양호): 정상 상태로 반납
  - `DAMAGED` (손상): 외관 손상이 있으나 사용 가능
  - `NEEDS_REPAIR` (수리필요): 수리가 필요한 상태, 자산 상태를 `IN_REPAIR`로 변경
- 반납 사유를 기록한다:
  - 퇴사
  - 교체 (신규 자산으로 교체)
  - 고장
  - 기타

### 2.3 자산 이동

#### 2.3.1 부서 간 이동 (재배정)

- 현재 배정된 사용자/부서에서 다른 사용자/부서로 자산을 이동한다.
- 기존 배정을 반납 처리한 후 새로운 배정을 생성하는 방식으로 처리한다.
- 이력에 `RETURNED` + `ASSIGNED` 두 건이 기록된다.

#### 2.3.2 위치 변경

- 자산의 물리적 위치를 변경한다.
- 배정 대상은 변경되지 않고 `assets.location` 필드만 업데이트한다.
- 이력에 `MOVED` 액션이 기록된다 (`from_value`: 이전 위치, `to_value`: 새 위치).

### 2.4 입사자 자산 체크리스트

- 입사자에게 배정해야 할 필수 자산 목록을 사전에 정의한다.
- 기본 체크리스트 항목 예시:
  - 노트북
  - 모니터
  - 키보드
  - 마우스
  - ID카드
  - 사무용 의자 (선택)
- 입사자별 체크리스트를 생성하고, 각 항목의 배정 완료 여부를 추적한다.
- 모든 항목이 완료되면 체크리스트 `completed_at`에 완료 일시를 기록한다.

### 2.5 퇴사자 자산 체크리스트

- 퇴사자에게 배정된 모든 자산의 반납 여부를 확인한다.
- 해당 사용자에게 현재 배정된 자산 목록(`is_active = true`)을 자동으로 불러온다.
- 각 자산별 반납 완료 여부를 체크한다.
- 미반납 자산이 있는 경우 퇴사 처리를 진행할 수 없도록 경고한다.

---

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 배정/반납 처리 응답시간 500ms 이내 |
| 동시성 | 동일 자산에 대한 동시 배정 요청 시 하나만 성공해야 함 (낙관적/비관적 잠금) |
| 정합성 | 배정 시 자산 상태 변경과 배정 레코드 생성이 하나의 트랜잭션으로 처리됨 |
| 보안 | 자산 배정/반납은 자산 관리자 또는 부서 관리자 권한 필요 |
| 보안 | 일반 사용자는 본인 배정 자산만 조회 가능 |
| 알림 | 배정/반납 시 대상 사용자에게 알림 (향후 알림 모듈 연동) |
| 데이터 | 배정/반납 이력은 소프트 삭제 불가 (감사 추적용) |

---

## 4. 데이터베이스 스키마

### 4.1 `asset_assignments` (자산 배정)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 배정 고유 식별자 |
| `asset_id` | `UUID` | NOT NULL, FK → `assets.id` | 배정 대상 자산 ID |
| `assignee_type` | `VARCHAR(20)` | NOT NULL | 배정 대상 유형 (`USER` / `DEPARTMENT`) |
| `assignee_id` | `UUID` | NOT NULL | 배정 대상 ID (사용자 또는 부서 UUID) |
| `assigned_by` | `UUID` | NOT NULL | 배정 처리자 ID |
| `assigned_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 배정 일시 (UTC) |
| `confirmed_at` | `TIMESTAMPTZ` | NULLABLE | 배정 확인(수령) 일시 |
| `returned_at` | `TIMESTAMPTZ` | NULLABLE | 반납 일시 (NULL이면 미반납) |
| `returned_by` | `UUID` | NULLABLE | 반납 처리자 ID |
| `return_reason` | `VARCHAR(50)` | NULLABLE | 반납 사유 (`RESIGNATION`/`REPLACEMENT`/`MALFUNCTION`/`OTHER`) |
| `return_condition` | `VARCHAR(20)` | NULLABLE | 반납 상태 점검 결과 |
| `return_note` | `TEXT` | NULLABLE | 반납 비고 |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | 현재 활성 배정 여부 |
| `created_by` | `UUID` | NOT NULL | 생성자 ID |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 생성 일시 (UTC) |
| `updated_by` | `UUID` | NULLABLE | 수정자 ID |
| `updated_at` | `TIMESTAMPTZ` | NULLABLE | 수정 일시 (UTC) |

**CHECK 제약조건**:
- `chk_assignee_type` CHECK (`assignee_type` IN (`'USER'`, `'DEPARTMENT'`))
- `chk_return_condition` CHECK (`return_condition` IN (`'GOOD'`, `'DAMAGED'`, `'NEEDS_REPAIR'`) OR `return_condition` IS NULL)
- `chk_return_reason` CHECK (`return_reason` IN (`'RESIGNATION'`, `'REPLACEMENT'`, `'MALFUNCTION'`, `'OTHER'`) OR `return_reason` IS NULL)

**유니크 제약조건**:
- `uq_asset_active_assignment` UNIQUE (`asset_id`) WHERE `is_active = TRUE` (부분 유니크 인덱스 - 활성 배정은 자산당 1건만 허용)

**인덱스**:
- `idx_asset_assignments_asset_id` ON `asset_id`
- `idx_asset_assignments_assignee` ON `assignee_type`, `assignee_id`
- `idx_asset_assignments_is_active` ON `asset_id` WHERE `is_active = TRUE`
- `idx_asset_assignments_assigned_at` ON `assigned_at`

### 4.2 `asset_checklists` (자산 체크리스트 템플릿)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 체크리스트 고유 식별자 |
| `name` | `VARCHAR(100)` | NOT NULL | 체크리스트명 (예: 신입사원 표준 장비) |
| `type` | `VARCHAR(20)` | NOT NULL | 유형 (`ONBOARDING` / `OFFBOARDING`) |
| `items_json` | `JSONB` | NOT NULL | 체크리스트 항목 목록 |
| `is_default` | `BOOLEAN` | NOT NULL, DEFAULT `FALSE` | 기본 체크리스트 여부 |
| `created_by` | `UUID` | NOT NULL | 생성자 ID |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 생성 일시 (UTC) |
| `updated_by` | `UUID` | NULLABLE | 수정자 ID |
| `updated_at` | `TIMESTAMPTZ` | NULLABLE | 수정 일시 (UTC) |
| `deleted_at` | `TIMESTAMPTZ` | NULLABLE | 소프트 삭제 일시 |

**CHECK 제약조건**:
- `chk_checklist_type` CHECK (`type` IN (`'ONBOARDING'`, `'OFFBOARDING'`))

**`items_json` 예시** (입사자 체크리스트):

```json
[
  { "key": "notebook", "label": "노트북", "required": true, "category_code": "NB" },
  { "key": "monitor", "label": "모니터", "required": true, "category_code": "MON" },
  { "key": "keyboard", "label": "키보드", "required": true, "category_code": "PER" },
  { "key": "mouse", "label": "마우스", "required": true, "category_code": "PER" },
  { "key": "id_card", "label": "ID카드", "required": true, "category_code": null },
  { "key": "chair", "label": "사무용 의자", "required": false, "category_code": null }
]
```

### 4.3 `asset_checklist_records` (체크리스트 실행 기록)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 기록 고유 식별자 |
| `checklist_id` | `UUID` | NOT NULL, FK → `asset_checklists.id` | 체크리스트 템플릿 ID |
| `user_id` | `UUID` | NOT NULL | 대상 사용자 ID (입사자/퇴사자) |
| `items_status_json` | `JSONB` | NOT NULL | 각 항목별 완료 상태 |
| `completed_at` | `TIMESTAMPTZ` | NULLABLE | 전체 완료 일시 (모든 필수 항목 완료 시) |
| `created_by` | `UUID` | NOT NULL | 생성자 ID |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 생성 일시 (UTC) |
| `updated_by` | `UUID` | NULLABLE | 수정자 ID |
| `updated_at` | `TIMESTAMPTZ` | NULLABLE | 수정 일시 (UTC) |
| `deleted_at` | `TIMESTAMPTZ` | NULLABLE | 소프트 삭제 일시 |

**인덱스**:
- `idx_checklist_records_user_id` ON `user_id`
- `idx_checklist_records_checklist_id` ON `checklist_id`

**`items_status_json` 예시**:

```json
[
  { "key": "notebook", "label": "노트북", "required": true, "completed": true, "asset_id": "uuid-asset-42", "completed_at": "2026-03-20T02:00:00Z", "completed_by": "uuid-admin" },
  { "key": "monitor", "label": "모니터", "required": true, "completed": true, "asset_id": "uuid-asset-55", "completed_at": "2026-03-20T02:10:00Z", "completed_by": "uuid-admin" },
  { "key": "keyboard", "label": "키보드", "required": true, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null },
  { "key": "mouse", "label": "마우스", "required": true, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null },
  { "key": "id_card", "label": "ID카드", "required": true, "completed": true, "asset_id": null, "completed_at": "2026-03-20T01:00:00Z", "completed_by": "uuid-admin" },
  { "key": "chair", "label": "사무용 의자", "required": false, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null }
]
```

---

## 5. API 명세

### 5.1 자산 배정

#### `POST /api/v1/assets/{id}/assign`

자산을 사용자 또는 부서에 배정한다.

**경로 파라미터**:
- `id`: 자산 UUID

**요청 본문**:

```json
{
  "assignee_type": "USER",
  "assignee_id": "uuid-user-kim",
  "note": "신규 입사자 장비 배정"
}
```

**응답 (201 Created)**:

```json
{
  "data": {
    "id": "uuid-assignment-1",
    "asset_id": "uuid-asset-42",
    "asset_number": "NB-2026-042",
    "assignee_type": "USER",
    "assignee_id": "uuid-user-kim",
    "assignee_name": "김개발",
    "assigned_by": "uuid-admin",
    "assigned_at": "2026-03-23T09:00:00Z",
    "confirmed_at": null,
    "is_active": true
  }
}
```

**에러 응답 (409 Conflict)**:

```json
{
  "error": {
    "code": "ASSET_NOT_AVAILABLE",
    "message": "해당 자산은 현재 배정 가능한 상태가 아닙니다. (현재 상태: IN_USE)"
  }
}
```

**에러 응답 (409 Conflict)**:

```json
{
  "error": {
    "code": "ASSET_ALREADY_ASSIGNED",
    "message": "해당 자산은 이미 다른 사용자에게 배정되어 있습니다."
  }
}
```

#### `POST /api/v1/assets/{id}/assign/confirm`

배정받은 사용자가 수령을 확인한다.

**응답 (200 OK)**:

```json
{
  "data": {
    "id": "uuid-assignment-1",
    "confirmed_at": "2026-03-23T10:00:00Z"
  }
}
```

### 5.2 자산 반납

#### `POST /api/v1/assets/{id}/return`

배정된 자산을 반납 처리한다.

**경로 파라미터**:
- `id`: 자산 UUID

**요청 본문**:

```json
{
  "return_reason": "REPLACEMENT",
  "return_condition": "GOOD",
  "return_note": "신규 장비 교체에 따른 기존 장비 반납"
}
```

**응답 (200 OK)**:

```json
{
  "data": {
    "id": "uuid-assignment-1",
    "asset_id": "uuid-asset-42",
    "asset_number": "NB-2026-042",
    "assignee_type": "USER",
    "assignee_id": "uuid-user-kim",
    "assignee_name": "김개발",
    "assigned_at": "2026-03-20T02:00:00Z",
    "returned_at": "2026-03-23T09:30:00Z",
    "return_reason": "REPLACEMENT",
    "return_condition": "GOOD",
    "return_note": "신규 장비 교체에 따른 기존 장비 반납",
    "is_active": false,
    "asset_status": "AVAILABLE"
  }
}
```

**`return_condition`이 `NEEDS_REPAIR`인 경우**:

```json
{
  "data": {
    "...": "...",
    "return_condition": "NEEDS_REPAIR",
    "return_note": "액정 파손, 수리 필요",
    "is_active": false,
    "asset_status": "IN_REPAIR"
  }
}
```

**에러 응답 (404 Not Found)**:

```json
{
  "error": {
    "code": "NO_ACTIVE_ASSIGNMENT",
    "message": "해당 자산에 활성 배정 내역이 없습니다."
  }
}
```

### 5.3 자산 이동 (재배정)

#### `POST /api/v1/assets/{id}/transfer`

현재 배정을 해제하고 새로운 대상에게 재배정한다.

**경로 파라미터**:
- `id`: 자산 UUID

**요청 본문**:

```json
{
  "new_assignee_type": "USER",
  "new_assignee_id": "uuid-user-lee",
  "new_location": "본사 6층 인프라팀",
  "note": "부서 이동에 따른 자산 재배정"
}
```

**응답 (200 OK)**:

```json
{
  "data": {
    "previous_assignment": {
      "id": "uuid-assignment-1",
      "assignee_name": "김개발",
      "returned_at": "2026-03-23T11:00:00Z"
    },
    "new_assignment": {
      "id": "uuid-assignment-2",
      "asset_id": "uuid-asset-42",
      "asset_number": "NB-2026-042",
      "assignee_type": "USER",
      "assignee_id": "uuid-user-lee",
      "assignee_name": "이인프라",
      "assigned_at": "2026-03-23T11:00:00Z",
      "is_active": true
    },
    "location": "본사 6층 인프라팀"
  }
}
```

### 5.4 사용자별 배정 자산 조회

#### `GET /api/v1/users/{id}/assets`

특정 사용자에게 배정된 자산 목록을 조회한다.

**경로 파라미터**:
- `id`: 사용자 UUID

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `active_only` | `boolean` | N | 현재 활성 배정만 조회 (기본값: `true`) |
| `page` | `integer` | N | 페이지 번호 (기본값: 1) |
| `size` | `integer` | N | 페이지 크기 (기본값: 20) |

**응답 (200 OK)**:

```json
{
  "data": [
    {
      "assignment_id": "uuid-assignment-2",
      "asset": {
        "id": "uuid-asset-42",
        "asset_number": "NB-2026-042",
        "name": "개발팀 노트북 #42",
        "category": { "id": "uuid-nb", "name": "노트북", "code": "NB" },
        "manufacturer": "Apple",
        "model": "MacBook Pro 16 (2025)",
        "serial_number": "C02XXXXXXXXX",
        "status": "IN_USE"
      },
      "assigned_at": "2026-03-20T02:00:00Z",
      "confirmed_at": "2026-03-20T03:00:00Z",
      "is_active": true
    },
    {
      "assignment_id": "uuid-assignment-5",
      "asset": {
        "id": "uuid-asset-55",
        "asset_number": "MON-2026-015",
        "name": "27인치 모니터",
        "category": { "id": "uuid-mon", "name": "모니터", "code": "MON" },
        "manufacturer": "LG",
        "model": "27UL850",
        "serial_number": "SN123456789",
        "status": "IN_USE"
      },
      "assigned_at": "2026-03-20T02:10:00Z",
      "confirmed_at": "2026-03-20T03:00:00Z",
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total_count": 2,
    "total_pages": 1
  }
}
```

### 5.5 자산 체크리스트

#### `GET /api/v1/asset-checklists`

체크리스트 템플릿 목록을 조회한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `type` | `string` | N | 유형 필터 (`ONBOARDING`/`OFFBOARDING`) |

**응답 (200 OK)**:

```json
{
  "data": [
    {
      "id": "uuid-cl-1",
      "name": "신입사원 표준 장비",
      "type": "ONBOARDING",
      "is_default": true,
      "items_json": [
        { "key": "notebook", "label": "노트북", "required": true, "category_code": "NB" },
        { "key": "monitor", "label": "모니터", "required": true, "category_code": "MON" },
        { "key": "keyboard", "label": "키보드", "required": true, "category_code": "PER" },
        { "key": "mouse", "label": "마우스", "required": true, "category_code": "PER" },
        { "key": "id_card", "label": "ID카드", "required": true, "category_code": null }
      ],
      "created_at": "2026-01-15T00:00:00Z"
    }
  ]
}
```

#### `POST /api/v1/asset-checklists`

새 체크리스트 템플릿을 생성한다.

**요청 본문**:

```json
{
  "name": "개발팀 입사자 장비",
  "type": "ONBOARDING",
  "is_default": false,
  "items_json": [
    { "key": "notebook", "label": "노트북 (MacBook Pro)", "required": true, "category_code": "NB" },
    { "key": "monitor_1", "label": "모니터 1", "required": true, "category_code": "MON" },
    { "key": "monitor_2", "label": "모니터 2 (듀얼)", "required": false, "category_code": "MON" },
    { "key": "keyboard", "label": "키보드", "required": true, "category_code": "PER" },
    { "key": "mouse", "label": "마우스", "required": true, "category_code": "PER" },
    { "key": "webcam", "label": "웹캠", "required": false, "category_code": "PER" },
    { "key": "id_card", "label": "ID카드", "required": true, "category_code": null }
  ]
}
```

**응답 (201 Created)**: 생성된 체크리스트 객체 반환

#### `PUT /api/v1/asset-checklists/{id}`

체크리스트 템플릿을 수정한다.

**요청 본문**: `POST`와 동일한 구조

**응답 (200 OK)**: 수정된 체크리스트 객체 반환

#### `DELETE /api/v1/asset-checklists/{id}`

체크리스트 템플릿을 소프트 삭제한다.

**응답 (204 No Content)**

### 5.6 체크리스트 실행 기록

#### `POST /api/v1/asset-checklists/{id}/records`

특정 사용자에 대해 체크리스트를 실행(생성)한다.

**경로 파라미터**:
- `id`: 체크리스트 템플릿 UUID

**요청 본문**:

```json
{
  "user_id": "uuid-user-new"
}
```

**응답 (201 Created)**:

```json
{
  "data": {
    "id": "uuid-record-1",
    "checklist_id": "uuid-cl-1",
    "checklist_name": "신입사원 표준 장비",
    "user_id": "uuid-user-new",
    "user_name": "박신입",
    "items_status_json": [
      { "key": "notebook", "label": "노트북", "required": true, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null },
      { "key": "monitor", "label": "모니터", "required": true, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null },
      { "key": "keyboard", "label": "키보드", "required": true, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null },
      { "key": "mouse", "label": "마우스", "required": true, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null },
      { "key": "id_card", "label": "ID카드", "required": true, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null }
    ],
    "completed_at": null,
    "created_at": "2026-03-23T09:00:00Z"
  }
}
```

#### `PATCH /api/v1/asset-checklists/records/{record_id}/items/{item_key}`

체크리스트 특정 항목의 완료 상태를 갱신한다.

**요청 본문**:

```json
{
  "completed": true,
  "asset_id": "uuid-asset-42"
}
```

**응답 (200 OK)**:

```json
{
  "data": {
    "id": "uuid-record-1",
    "items_status_json": [
      { "key": "notebook", "label": "노트북", "required": true, "completed": true, "asset_id": "uuid-asset-42", "completed_at": "2026-03-23T09:30:00Z", "completed_by": "uuid-admin" },
      { "key": "monitor", "label": "모니터", "required": true, "completed": false, "asset_id": null, "completed_at": null, "completed_by": null },
      "..."
    ],
    "completed_at": null
  }
}
```

> 모든 필수 항목이 완료되면 `completed_at`에 현재 시각이 자동 설정된다.

#### `GET /api/v1/asset-checklists/records`

체크리스트 실행 기록 목록을 조회한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `user_id` | `UUID` | N | 대상 사용자 필터 |
| `checklist_type` | `string` | N | 유형 필터 (`ONBOARDING`/`OFFBOARDING`) |
| `completed` | `boolean` | N | 완료 여부 필터 |
| `page` | `integer` | N | 페이지 번호 (기본값: 1) |
| `size` | `integer` | N | 페이지 크기 (기본값: 20) |

**응답 (200 OK)**: 페이지네이션된 체크리스트 기록 목록

---

## 6. 화면 설계

### 6.1 자산 배정 폼 (`/inventories/assets/{id}/assign`)

```
┌─────────────────────────────────────────────────────────────────┐
│ 자산 배정                                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ 배정 대상 자산 ─────────────────────────────────────────┐   │
│  │ 자산번호   NB-2026-042                                    │   │
│  │ 자산명     개발팀 노트북 #42                               │   │
│  │ 분류       하드웨어 > 노트북                               │   │
│  │ 상태       ● 여유 (AVAILABLE)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  배정 유형     (●) 개인 배정    ( ) 부서 배정                     │
│                                                                 │
│  ┌─ 개인 배정 ──────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  사용자 검색  [김개발_________________ 🔍]                 │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │ 👤 김개발 (kim@company.com)                       │    │   │
│  │  │    개발팀 / 백엔드파트                              │    │   │
│  │  │    현재 배정 자산: 2건                              │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  │  비고  [____________________________________]            │   │
│  │        [____________________________________]            │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│                                      [취소]  [배정 처리]         │
└─────────────────────────────────────────────────────────────────┘
```

- 사용자 검색 시 이름/이메일/사번으로 검색 가능
- 검색 결과에 현재 소속 부서와 기존 배정 자산 수 표시
- 부서 배정 선택 시 조직도 트리에서 부서 선택

### 6.2 반납 처리 폼 (`/inventories/assets/{id}/return`)

```
┌─────────────────────────────────────────────────────────────────┐
│ 자산 반납                                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ 반납 대상 자산 ─────────────────────────────────────────┐   │
│  │ 자산번호   NB-2026-042                                    │   │
│  │ 자산명     개발팀 노트북 #42                               │   │
│  │ 현재 배정  김개발 (개발팀)   배정일: 2026-03-20            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ── 반납 정보 ──                                                 │
│                                                                 │
│  반납 사유     [퇴사           ▼]                                │
│               ( ) 퇴사                                          │
│               ( ) 교체 (신규 자산으로 교체)                       │
│               ( ) 고장                                          │
│               ( ) 기타                                          │
│                                                                 │
│  ── 상태 점검 ──                                                 │
│                                                                 │
│  반납 상태     (●) 양호        ( ) 손상        ( ) 수리필요       │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ ⚠ "수리필요" 선택 시 자산 상태가 '수리중'으로 변경됩니다.  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  반납 비고     [____________________________________]           │
│               [____________________________________]           │
│                                                                 │
│                                      [취소]  [반납 처리]         │
└─────────────────────────────────────────────────────────────────┘
```

- "수리필요" 선택 시 안내 메시지 표시
- 반납 완료 후 자산 상세 페이지로 이동

### 6.3 내 자산 목록 페이지 (`/inventories/my-assets`)

일반 사용자가 본인에게 배정된 자산을 확인하는 페이지.

```
┌─────────────────────────────────────────────────────────────────┐
│ 내 자산 목록                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  현재 배정된 자산 (3건)                                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🖥 NB-2026-042  개발팀 노트북 #42                        │   │
│  │   Apple MacBook Pro 16 (2025)                            │   │
│  │   배정일: 2026-03-20   수령확인: 완료                      │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ 🖥 MON-2026-015  27인치 모니터                            │   │
│  │   LG 27UL850                                             │   │
│  │   배정일: 2026-03-20   수령확인: 완료                      │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ ⌨ PER-2026-088  무선 키보드/마우스 세트                    │   │
│  │   Logitech MX Keys Combo                                 │   │
│  │   배정일: 2026-03-20   수령확인: [확인하기]                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ── 과거 배정 이력 ──                                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ NB-2025-033  이전 노트북                                  │   │
│  │ 배정: 2025-06-01 ~ 2026-03-19   반납사유: 교체            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

- 카드형 레이아웃으로 배정 자산 표시
- 미확인 배정은 [확인하기] 버튼 노출
- 하단에 과거 배정 이력 표시 (접기/펼치기)

### 6.4 입퇴사 체크리스트 관리 화면 (`/inventories/checklists`)

```
┌─────────────────────────────────────────────────────────────────┐
│ 자산 체크리스트                                  [+ 체크리스트 생성]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [입사(ONBOARDING)]  [퇴사(OFFBOARDING)]                          │
│                                                                 │
│ ┌───┬────────────────────┬──────┬─────┬──────┬───────────────┐ │
│ │   │ 체크리스트명         │ 유형 │ 항목 │ 기본 │ 관리           │ │
│ ├───┼────────────────────┼──────┼─────┼──────┼───────────────┤ │
│ │ 1 │ 신입사원 표준 장비   │ 입사 │ 5건 │ ✓   │ [수정] [삭제]  │ │
│ │ 2 │ 개발팀 입사자 장비   │ 입사 │ 7건 │     │ [수정] [삭제]  │ │
│ │ 3 │ 퇴사자 자산 반납     │ 퇴사 │ -   │ ✓   │ [수정] [삭제]  │ │
│ └───┴────────────────────┴──────┴─────┴──────┴───────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.5 체크리스트 실행 화면 (`/inventories/checklists/records/{id}`)

```
┌─────────────────────────────────────────────────────────────────┐
│ 입사자 자산 체크리스트                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  대상자:  박신입 (개발팀)          입사일: 2026-03-25              │
│  템플릿:  신입사원 표준 장비        진행률: ████░░░░ 2/5           │
│                                                                 │
│  ┌───┬──────┬──────┬────────────────────────┬──────┬────────┐  │
│  │   │ 항목  │ 필수 │ 배정 자산               │ 상태 │ 처리    │  │
│  ├───┼──────┼──────┼────────────────────────┼──────┼────────┤  │
│  │ ✓ │노트북 │  ●  │ NB-2026-042 MacBook..  │ 완료 │         │  │
│  │ ✓ │모니터 │  ●  │ MON-2026-055 LG 27..  │ 완료 │         │  │
│  │   │키보드 │  ●  │ -                      │ 미완 │ [배정]  │  │
│  │   │마우스 │  ●  │ -                      │ 미완 │ [배정]  │  │
│  │   │ID카드 │  ●  │ -                      │ 미완 │ [완료]  │  │
│  └───┴──────┴──────┴────────────────────────┴──────┴────────┘  │
│                                                                 │
│  ⚠ 필수 항목 3건이 미완료 상태입니다.                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

- [배정] 클릭 시 해당 카테고리의 여유(`AVAILABLE`) 자산 목록에서 선택하여 즉시 배정
- [완료] 클릭 시 자산 연동 없이 항목만 완료 처리 (ID카드 등 시스템 외 자산)
- 진행률 바로 전체 완료 현황 시각화

---

## 7. 인수 조건

### 7.1 자산 배정

- [ ] `AVAILABLE` 상태의 자산을 특정 사용자에게 배정할 수 있다.
- [ ] `AVAILABLE` 상태의 자산을 특정 부서에 공용 배정할 수 있다.
- [ ] 배정 시 자산 상태가 `IN_USE`로 자동 변경된다.
- [ ] 배정 시 `asset_history`에 `ASSIGNED` 액션이 기록된다.
- [ ] 이미 배정된 자산(`IN_USE`)은 중복 배정할 수 없다.
- [ ] 배정받은 사용자가 수령 확인을 할 수 있다.
- [ ] 미확인 배정 목록을 관리자가 조회할 수 있다.

### 7.2 자산 반납

- [ ] 배정된 자산을 반납 처리할 수 있다.
- [ ] 반납 시 반납 사유(퇴사/교체/고장/기타)를 선택할 수 있다.
- [ ] 반납 시 상태 점검 결과(양호/손상/수리필요)를 기록할 수 있다.
- [ ] 반납 상태가 "양호" 또는 "손상"이면 자산 상태가 `AVAILABLE`로 변경된다.
- [ ] 반납 상태가 "수리필요"이면 자산 상태가 `IN_REPAIR`로 변경된다.
- [ ] 반납 시 `asset_history`에 `RETURNED` 액션이 기록된다.
- [ ] `is_active`가 `FALSE`로 변경되고 `returned_at`에 반납 일시가 기록된다.

### 7.3 자산 이동

- [ ] 현재 배정된 자산을 다른 사용자/부서로 재배정(이동)할 수 있다.
- [ ] 재배정 시 기존 배정이 반납 처리되고 새 배정이 생성된다.
- [ ] 자산의 물리적 위치만 변경할 수 있으며, 이력에 `MOVED` 액션이 기록된다.

### 7.4 내 자산 조회

- [ ] 일반 사용자가 본인에게 배정된 자산 목록을 조회할 수 있다.
- [ ] 과거 배정 이력도 함께 확인할 수 있다.

### 7.5 체크리스트

- [ ] 관리자가 입사/퇴사 체크리스트 템플릿을 생성/수정/삭제할 수 있다.
- [ ] 특정 사용자에 대해 체크리스트를 실행(생성)할 수 있다.
- [ ] 체크리스트 항목별 자산 배정 또는 완료 처리를 할 수 있다.
- [ ] 자산 카테고리와 연동된 항목은 해당 카테고리의 `AVAILABLE` 자산에서 선택하여 배정한다.
- [ ] 모든 필수 항목이 완료되면 체크리스트가 자동 완료 처리된다.
- [ ] 퇴사 체크리스트에서 미반납 자산이 있으면 경고를 표시한다.

---

## 8. 참고사항

- 배정/반납 처리는 트랜잭션으로 묶어 `asset_assignments` 레코드 생성/수정, `assets.status` 변경, `asset_history` 기록이 원자적으로 처리되어야 한다.
- 동시 배정 방지를 위해 자산 행에 대한 비관적 잠금(`SELECT ... FOR UPDATE`)을 사용한다.
- `asset_assignments` 테이블의 부분 유니크 인덱스(`is_active = TRUE`)로 데이터베이스 수준에서도 중복 배정을 방지한다.
- 사용자/부서 정보는 `01-02` 사용자 관리, `01-03` 조직도 모듈의 API를 호출하여 조회한다. 직접 조인하지 않고 API 기반으로 연동한다.
- 배정 확인서는 현재 시스템 내 확인(클릭) 방식이며, 전자서명이나 출력 기능은 향후 확장으로 검토한다.
- 퇴사 체크리스트는 인사(HR) 모듈과 연동하여 퇴사 프로세스의 일부로 포함될 수 있다. 현재는 독립적으로 운영한다.
- 대량 배정(엑셀 업로드를 통한 일괄 배정)은 향후 확장으로 검토한다.
