# 05-01 자산 등록 및 분류

## 1. 개요

그룹웨어 자산관리 모듈의 핵심 기능으로, 조직이 보유한 모든 자산(하드웨어/소프트웨어)을 체계적으로 등록하고 분류하는 기능을 제공한다. 자산번호 자동 채번, 계층적 카테고리 분류, 상태 관리, 이력 추적 등을 통해 자산의 전 생애주기를 관리한다.

- **모듈**: 자산관리 (Inventories)
- **의존성**: `01-04` 권한 관리
- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)

---

## 2. 기능 요구사항

### 2.1 자산 분류 체계 (카테고리 관리)

계층적 카테고리 구조를 지원하며, 관리자가 카테고리를 추가/수정/삭제할 수 있다.

| 대분류 | 중분류 | 코드 |
|--------|--------|------|
| 하드웨어 | 서버 (물리 서버, 가상 서버) | `SVR` |
| 하드웨어 | 네트워크 장비 (스위치, 라우터, AP) | `NET` |
| 하드웨어 | 데스크톱 | `DT` |
| 하드웨어 | 노트북 | `NB` |
| 하드웨어 | 모니터 | `MON` |
| 하드웨어 | 프린터 | `PRT` |
| 하드웨어 | 스캐너 | `SCN` |
| 하드웨어 | 기타 주변기기 (키보드, 마우스, 웹캠 등) | `PER` |
| 소프트웨어 | OS 라이선스 | `SOS` |
| 소프트웨어 | 오피스 라이선스 | `SOF` |
| 소프트웨어 | 개발도구 라이선스 | `SDV` |
| 소프트웨어 | 기타 소프트웨어 | `SET` |

- 카테고리별 스펙 스키마(JSON Schema)를 정의하여, 해당 카테고리 자산 등록 시 입력해야 할 스펙 항목을 동적으로 결정한다.
- 최대 3단계 계층 지원 (대분류 > 중분류 > 소분류)

### 2.2 자산 등록

- **자산번호 자동 채번**: `{카테고리코드}-{연도(4자리)}-{순번(3자리, 0패딩)}`
  - 예: `SVR-2026-001`, `NB-2026-042`, `MON-2026-103`
  - 연도 기준은 등록일 기준 UTC
  - 순번은 카테고리코드 + 연도 조합별 자동 증가
- **기본 정보**: 자산명, 카테고리, 제조사, 모델명, 시리얼번호
- **구매 정보**: 구매일, 구매처, 구매가격(원화)
- **스펙 정보**: 카테고리별 동적 JSON (예: 서버 - CPU, RAM, Storage, OS / 노트북 - CPU, RAM, Storage, 화면크기 등)
- **위치 정보**: 사무실/서버실, 층/구역
- **보증 정보**: 보증 만료일 (`warranty_expires_at`)
- **자산 이미지**: 사진 업로드 (최대 5장, 각 10MB 이하, JPG/PNG)
- **비고**: 자유 텍스트 메모

### 2.3 자산 상태 관리

| 상태 | 코드 | 설명 |
|------|------|------|
| 사용중 | `IN_USE` | 사용자 또는 부서에 배정되어 사용 중 |
| 여유 | `AVAILABLE` | 배정되지 않은 사용 가능 상태 |
| 수리중 | `IN_REPAIR` | 수리/점검을 위해 일시적으로 사용 불가 |
| 폐기 | `DISPOSED` | 내용연수 경과 또는 고장으로 폐기 처리 |
| 분실 | `LOST` | 분실 신고된 자산 |

- 상태 변경 시 반드시 이력이 기록된다.
- 폐기(`DISPOSED`) 상태의 자산은 재활성화할 수 없다.

### 2.4 자산 이력 관리

모든 자산 변경사항을 시간순으로 기록한다.

| 액션 | 코드 | 설명 |
|------|------|------|
| 등록 | `REGISTERED` | 자산 최초 등록 |
| 배정 | `ASSIGNED` | 사용자/부서에 배정 |
| 반납 | `RETURNED` | 배정 해제 및 반납 |
| 수리 | `REPAIRED` | 수리 완료 기록 |
| 이동 | `MOVED` | 위치 변경 |
| 상태변경 | `STATUS_CHANGED` | 상태 값 변경 |
| 폐기 | `DISPOSED` | 폐기 처리 |

- `from_value` / `to_value`로 변경 전/후 값을 기록한다.
- 수행자(`performed_by`)와 수행 시각(`performed_at`)을 반드시 기록한다.

---

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 자산 목록 조회 1,000건 기준 응답시간 500ms 이내 |
| 성능 | 자산 검색 (필터 + 페이지네이션) 응답시간 300ms 이내 |
| 확장성 | 자산 10만 건 이상 등록 시에도 안정적 운영 |
| 보안 | 자산 등록/수정/삭제는 권한(`01-04`)에 따라 제어 |
| 보안 | 자산 이력은 수정/삭제 불가 (Immutable) |
| 이미지 | 업로드 파일 크기 제한 10MB, 허용 포맷 JPG/PNG |
| 데이터 | 자산번호는 시스템 내 유일해야 함 (UNIQUE) |
| 데이터 | 삭제는 소프트 삭제(soft delete) 방식 적용 |

---

## 4. 데이터베이스 스키마

### 4.1 `asset_categories` (자산 카테고리)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 카테고리 고유 식별자 |
| `name` | `VARCHAR(100)` | NOT NULL | 카테고리명 (예: 노트북) |
| `code` | `VARCHAR(10)` | NOT NULL, UNIQUE | 카테고리 코드 (예: NB) |
| `parent_id` | `UUID` | FK → `asset_categories.id`, NULLABLE | 상위 카테고리 ID (NULL이면 최상위) |
| `level` | `SMALLINT` | NOT NULL, DEFAULT 1 | 계층 레벨 (1: 대분류, 2: 중분류, 3: 소분류) |
| `sort_order` | `INTEGER` | NOT NULL, DEFAULT 0 | 정렬 순서 |
| `spec_schema_json` | `JSONB` | NULLABLE | 해당 카테고리의 스펙 입력 JSON Schema |
| `created_by` | `UUID` | NOT NULL | 생성자 ID |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 생성 일시 (UTC) |
| `updated_by` | `UUID` | NULLABLE | 수정자 ID |
| `updated_at` | `TIMESTAMPTZ` | NULLABLE | 수정 일시 (UTC) |
| `deleted_at` | `TIMESTAMPTZ` | NULLABLE | 소프트 삭제 일시 |

**인덱스**:
- `idx_asset_categories_parent_id` ON `parent_id`
- `idx_asset_categories_code` ON `code` WHERE `deleted_at IS NULL`

**`spec_schema_json` 예시** (노트북 카테고리):

```json
{
  "type": "object",
  "properties": {
    "cpu": { "type": "string", "title": "CPU", "description": "프로세서 모델명" },
    "ram": { "type": "string", "title": "RAM", "description": "메모리 용량 (예: 16GB)" },
    "storage": { "type": "string", "title": "저장장치", "description": "저장장치 종류 및 용량 (예: SSD 512GB)" },
    "display_size": { "type": "string", "title": "화면 크기", "description": "화면 크기 (예: 15.6인치)" },
    "os": { "type": "string", "title": "운영체제", "description": "설치된 OS" }
  },
  "required": ["cpu", "ram", "storage"]
}
```

### 4.2 `assets` (자산)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 자산 고유 식별자 |
| `asset_number` | `VARCHAR(20)` | NOT NULL, UNIQUE | 자산번호 (자동 채번) |
| `category_id` | `UUID` | NOT NULL, FK → `asset_categories.id` | 카테고리 ID |
| `name` | `VARCHAR(200)` | NOT NULL | 자산명 |
| `manufacturer` | `VARCHAR(100)` | NULLABLE | 제조사 |
| `model` | `VARCHAR(100)` | NULLABLE | 모델명 |
| `serial_number` | `VARCHAR(100)` | NULLABLE | 시리얼번호 |
| `spec_json` | `JSONB` | NULLABLE | 상세 스펙 (카테고리 스키마 기반) |
| `purchase_date` | `DATE` | NULLABLE | 구매일 |
| `purchase_price` | `NUMERIC(15,2)` | NULLABLE | 구매가격 (원) |
| `vendor` | `VARCHAR(200)` | NULLABLE | 구매처 |
| `location` | `VARCHAR(200)` | NULLABLE | 위치 (사무실/서버실/층/구역) |
| `warranty_expires_at` | `DATE` | NULLABLE | 보증 만료일 |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT `'AVAILABLE'` | 자산 상태 |
| `image_url` | `TEXT` | NULLABLE | 대표 이미지 URL |
| `note` | `TEXT` | NULLABLE | 비고 |
| `created_by` | `UUID` | NOT NULL | 생성자 ID |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 생성 일시 (UTC) |
| `updated_by` | `UUID` | NULLABLE | 수정자 ID |
| `updated_at` | `TIMESTAMPTZ` | NULLABLE | 수정 일시 (UTC) |
| `deleted_at` | `TIMESTAMPTZ` | NULLABLE | 소프트 삭제 일시 |

**CHECK 제약조건**:
- `chk_assets_status` CHECK (`status` IN (`'IN_USE'`, `'AVAILABLE'`, `'IN_REPAIR'`, `'DISPOSED'`, `'LOST'`))

**인덱스**:
- `idx_assets_asset_number` ON `asset_number` WHERE `deleted_at IS NULL`
- `idx_assets_category_id` ON `category_id`
- `idx_assets_status` ON `status` WHERE `deleted_at IS NULL`
- `idx_assets_serial_number` ON `serial_number` WHERE `deleted_at IS NULL`
- `idx_assets_warranty_expires_at` ON `warranty_expires_at` WHERE `deleted_at IS NULL`

### 4.3 `asset_images` (자산 이미지)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 이미지 고유 식별자 |
| `asset_id` | `UUID` | NOT NULL, FK → `assets.id` | 자산 ID |
| `image_url` | `TEXT` | NOT NULL | 이미지 저장 경로/URL |
| `is_primary` | `BOOLEAN` | NOT NULL, DEFAULT `FALSE` | 대표 이미지 여부 |
| `sort_order` | `INTEGER` | NOT NULL, DEFAULT 0 | 정렬 순서 |
| `created_by` | `UUID` | NOT NULL | 업로드자 ID |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 업로드 일시 (UTC) |
| `deleted_at` | `TIMESTAMPTZ` | NULLABLE | 소프트 삭제 일시 |

**인덱스**:
- `idx_asset_images_asset_id` ON `asset_id` WHERE `deleted_at IS NULL`

### 4.4 `asset_history` (자산 이력)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 이력 고유 식별자 |
| `asset_id` | `UUID` | NOT NULL, FK → `assets.id` | 자산 ID |
| `action` | `VARCHAR(20)` | NOT NULL | 액션 코드 |
| `from_value` | `TEXT` | NULLABLE | 변경 전 값 |
| `to_value` | `TEXT` | NULLABLE | 변경 후 값 |
| `performed_by` | `UUID` | NOT NULL | 수행자 ID |
| `performed_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 수행 일시 (UTC) |
| `note` | `TEXT` | NULLABLE | 비고 |

**CHECK 제약조건**:
- `chk_asset_history_action` CHECK (`action` IN (`'REGISTERED'`, `'ASSIGNED'`, `'RETURNED'`, `'REPAIRED'`, `'MOVED'`, `'STATUS_CHANGED'`, `'DISPOSED'`))

**인덱스**:
- `idx_asset_history_asset_id` ON `asset_id`
- `idx_asset_history_performed_at` ON `performed_at`

> **참고**: `asset_history` 테이블은 감사(audit) 목적이므로 `UPDATE`/`DELETE` 권한을 부여하지 않는다. `deleted_at` 컬럼 없음.

---

## 5. API 명세

### 5.1 자산 카테고리

#### `GET /api/v1/asset-categories`

카테고리 트리 전체를 조회한다.

**응답 (200 OK)**:

```json
{
  "data": [
    {
      "id": "uuid-hw",
      "name": "하드웨어",
      "code": "HW",
      "parent_id": null,
      "level": 1,
      "sort_order": 1,
      "spec_schema_json": null,
      "children": [
        {
          "id": "uuid-svr",
          "name": "서버",
          "code": "SVR",
          "parent_id": "uuid-hw",
          "level": 2,
          "sort_order": 1,
          "spec_schema_json": { "type": "object", "properties": { "cpu": { "type": "string" } } },
          "children": []
        },
        {
          "id": "uuid-nb",
          "name": "노트북",
          "code": "NB",
          "parent_id": "uuid-hw",
          "level": 2,
          "sort_order": 4,
          "spec_schema_json": { "type": "object", "properties": { "cpu": { "type": "string" }, "ram": { "type": "string" } } },
          "children": []
        }
      ]
    }
  ]
}
```

#### `POST /api/v1/asset-categories`

새 카테고리를 생성한다.

**요청 본문**:

```json
{
  "name": "노트북",
  "code": "NB",
  "parent_id": "uuid-hw",
  "sort_order": 4,
  "spec_schema_json": {
    "type": "object",
    "properties": {
      "cpu": { "type": "string", "title": "CPU" },
      "ram": { "type": "string", "title": "RAM" },
      "storage": { "type": "string", "title": "저장장치" }
    },
    "required": ["cpu", "ram", "storage"]
  }
}
```

**응답 (201 Created)**:

```json
{
  "data": {
    "id": "uuid-nb",
    "name": "노트북",
    "code": "NB",
    "parent_id": "uuid-hw",
    "level": 2,
    "sort_order": 4,
    "spec_schema_json": { "..." : "..." },
    "created_at": "2026-03-23T09:00:00Z"
  }
}
```

#### `PUT /api/v1/asset-categories/{id}`

카테고리 정보를 수정한다.

**요청 본문**:

```json
{
  "name": "노트북 (Laptop)",
  "sort_order": 5,
  "spec_schema_json": { "..." : "..." }
}
```

**응답 (200 OK)**: 수정된 카테고리 객체 반환

#### `DELETE /api/v1/asset-categories/{id}`

카테고리를 소프트 삭제한다. 하위 카테고리 또는 연결된 자산이 있는 경우 삭제 불가.

**응답 (204 No Content)**

**에러 응답 (409 Conflict)**:

```json
{
  "error": {
    "code": "CATEGORY_HAS_CHILDREN",
    "message": "하위 카테고리가 존재하여 삭제할 수 없습니다."
  }
}
```

### 5.2 자산

#### `POST /api/v1/assets`

새 자산을 등록한다. 자산번호는 서버에서 자동 채번한다.

**요청 본문**:

```json
{
  "category_id": "uuid-nb",
  "name": "개발팀 노트북 #42",
  "manufacturer": "Apple",
  "model": "MacBook Pro 16 (2025)",
  "serial_number": "C02XXXXXXXXX",
  "spec_json": {
    "cpu": "Apple M4 Pro",
    "ram": "36GB",
    "storage": "SSD 1TB",
    "display_size": "16.2인치",
    "os": "macOS Sequoia"
  },
  "purchase_date": "2026-03-15",
  "purchase_price": 3990000,
  "vendor": "(주)맥코리아",
  "location": "본사 5층 개발팀",
  "warranty_expires_at": "2029-03-15",
  "note": "개발팀 신규 입사자용"
}
```

**응답 (201 Created)**:

```json
{
  "data": {
    "id": "uuid-asset-1",
    "asset_number": "NB-2026-042",
    "category_id": "uuid-nb",
    "name": "개발팀 노트북 #42",
    "manufacturer": "Apple",
    "model": "MacBook Pro 16 (2025)",
    "serial_number": "C02XXXXXXXXX",
    "spec_json": { "cpu": "Apple M4 Pro", "ram": "36GB", "storage": "SSD 1TB", "display_size": "16.2인치", "os": "macOS Sequoia" },
    "purchase_date": "2026-03-15",
    "purchase_price": 3990000,
    "vendor": "(주)맥코리아",
    "location": "본사 5층 개발팀",
    "warranty_expires_at": "2029-03-15",
    "status": "AVAILABLE",
    "image_url": null,
    "note": "개발팀 신규 입사자용",
    "created_at": "2026-03-23T09:00:00Z"
  }
}
```

#### `GET /api/v1/assets`

자산 목록을 페이지네이션으로 조회한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `page` | `integer` | N | 페이지 번호 (기본값: 1) |
| `size` | `integer` | N | 페이지 크기 (기본값: 20, 최대: 100) |
| `category_id` | `UUID` | N | 카테고리 필터 |
| `status` | `string` | N | 상태 필터 (복수 가능, 콤마 구분) |
| `location` | `string` | N | 위치 필터 (부분 일치) |
| `sort_by` | `string` | N | 정렬 기준 (기본값: `created_at`) |
| `sort_order` | `string` | N | 정렬 방향 (`asc`/`desc`, 기본값: `desc`) |

**응답 (200 OK)**:

```json
{
  "data": [
    {
      "id": "uuid-asset-1",
      "asset_number": "NB-2026-042",
      "category": { "id": "uuid-nb", "name": "노트북", "code": "NB" },
      "name": "개발팀 노트북 #42",
      "manufacturer": "Apple",
      "model": "MacBook Pro 16 (2025)",
      "status": "AVAILABLE",
      "location": "본사 5층 개발팀",
      "created_at": "2026-03-23T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total_count": 156,
    "total_pages": 8
  }
}
```

#### `GET /api/v1/assets/search`

자산을 키워드로 검색한다. 자산번호, 자산명, 제조사, 모델명, 시리얼번호를 대상으로 한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `q` | `string` | Y | 검색 키워드 (최소 2자) |
| `page` | `integer` | N | 페이지 번호 (기본값: 1) |
| `size` | `integer` | N | 페이지 크기 (기본값: 20) |

**응답 (200 OK)**: `GET /api/v1/assets`와 동일한 형식

#### `GET /api/v1/assets/{id}`

자산 상세 정보를 조회한다. 카테고리 정보와 현재 배정 정보를 포함한다.

**응답 (200 OK)**:

```json
{
  "data": {
    "id": "uuid-asset-1",
    "asset_number": "NB-2026-042",
    "category": {
      "id": "uuid-nb",
      "name": "노트북",
      "code": "NB",
      "path": ["하드웨어", "노트북"]
    },
    "name": "개발팀 노트북 #42",
    "manufacturer": "Apple",
    "model": "MacBook Pro 16 (2025)",
    "serial_number": "C02XXXXXXXXX",
    "spec_json": {
      "cpu": "Apple M4 Pro",
      "ram": "36GB",
      "storage": "SSD 1TB",
      "display_size": "16.2인치",
      "os": "macOS Sequoia"
    },
    "purchase_date": "2026-03-15",
    "purchase_price": 3990000,
    "vendor": "(주)맥코리아",
    "location": "본사 5층 개발팀",
    "warranty_expires_at": "2029-03-15",
    "status": "IN_USE",
    "images": [
      { "id": "uuid-img-1", "image_url": "/uploads/assets/uuid-asset-1/photo1.jpg", "is_primary": true }
    ],
    "current_assignment": {
      "assignee_type": "USER",
      "assignee_id": "uuid-user-kim",
      "assignee_name": "김개발",
      "assigned_at": "2026-03-20T02:00:00Z"
    },
    "note": "개발팀 신규 입사자용",
    "created_at": "2026-03-23T09:00:00Z",
    "updated_at": null
  }
}
```

#### `PUT /api/v1/assets/{id}`

자산 정보를 수정한다. 변경된 필드만 전송 가능 (Partial Update).

**요청 본문**:

```json
{
  "location": "본사 6층 인프라팀",
  "note": "인프라팀으로 이동"
}
```

**응답 (200 OK)**: 수정된 자산 객체 반환

#### `DELETE /api/v1/assets/{id}`

자산을 소프트 삭제한다. `IN_USE` 상태의 자산은 삭제 불가.

**응답 (204 No Content)**

**에러 응답 (409 Conflict)**:

```json
{
  "error": {
    "code": "ASSET_IN_USE",
    "message": "사용중인 자산은 삭제할 수 없습니다. 먼저 반납 처리를 진행해주세요."
  }
}
```

#### `PATCH /api/v1/assets/{id}/status`

자산 상태를 변경한다. 이력이 자동으로 기록된다.

**요청 본문**:

```json
{
  "status": "IN_REPAIR",
  "note": "화면 깜빡임 현상으로 수리 접수"
}
```

**응답 (200 OK)**:

```json
{
  "data": {
    "id": "uuid-asset-1",
    "asset_number": "NB-2026-042",
    "status": "IN_REPAIR",
    "previous_status": "IN_USE"
  }
}
```

### 5.3 자산 이력

#### `GET /api/v1/assets/{id}/history`

특정 자산의 이력을 시간순(최신순)으로 조회한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `page` | `integer` | N | 페이지 번호 (기본값: 1) |
| `size` | `integer` | N | 페이지 크기 (기본값: 20) |
| `action` | `string` | N | 액션 타입 필터 |

**응답 (200 OK)**:

```json
{
  "data": [
    {
      "id": "uuid-hist-3",
      "action": "STATUS_CHANGED",
      "from_value": "IN_USE",
      "to_value": "IN_REPAIR",
      "performed_by": { "id": "uuid-user-admin", "name": "관리자" },
      "performed_at": "2026-03-22T08:30:00Z",
      "note": "화면 깜빡임 현상으로 수리 접수"
    },
    {
      "id": "uuid-hist-2",
      "action": "ASSIGNED",
      "from_value": null,
      "to_value": "김개발 (개발팀)",
      "performed_by": { "id": "uuid-user-admin", "name": "관리자" },
      "performed_at": "2026-03-20T02:00:00Z",
      "note": null
    },
    {
      "id": "uuid-hist-1",
      "action": "REGISTERED",
      "from_value": null,
      "to_value": null,
      "performed_by": { "id": "uuid-user-admin", "name": "관리자" },
      "performed_at": "2026-03-19T09:00:00Z",
      "note": "신규 자산 등록"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total_count": 3,
    "total_pages": 1
  }
}
```

### 5.4 자산 이미지

#### `POST /api/v1/assets/{id}/image`

자산 이미지를 업로드한다. `multipart/form-data` 형식.

**요청**:
- `Content-Type`: `multipart/form-data`
- `file`: 이미지 파일 (JPG/PNG, 최대 10MB)
- `is_primary`: `boolean` (선택, 기본값 false)

**응답 (201 Created)**:

```json
{
  "data": {
    "id": "uuid-img-1",
    "asset_id": "uuid-asset-1",
    "image_url": "/uploads/assets/uuid-asset-1/photo1.jpg",
    "is_primary": true,
    "created_at": "2026-03-23T09:10:00Z"
  }
}
```

#### `DELETE /api/v1/assets/{id}/image/{image_id}`

자산 이미지를 삭제한다.

**응답 (204 No Content)**

---

## 6. 화면 설계

### 6.1 자산 목록 화면 (`/inventories/assets`)

```
┌─────────────────────────────────────────────────────────────────┐
│ 자산 관리                                            [+ 자산 등록] │
├─────────────────────────────────────────────────────────────────┤
│ 검색: [__________________ 🔍]                                    │
│                                                                 │
│ 필터: [카테고리 ▼] [상태 ▼] [위치 ▼]              [필터 초기화]    │
├─────────────────────────────────────────────────────────────────┤
│ ┌───┬──────────┬──────┬───────┬────────┬──────┬──────┬──────┐  │
│ │ □ │ 자산번호  │ 분류 │ 자산명 │ 제조사  │ 상태 │ 위치  │ 등록일│  │
│ ├───┼──────────┼──────┼───────┼────────┼──────┼──────┼──────┤  │
│ │ □ │NB-2026-042│노트북│개발팀..│ Apple  │●사용중│5층   │03-23 │  │
│ │ □ │MON-2026-15│모니터│회의실..│  LG    │●여유  │3층   │03-22 │  │
│ │ □ │SVR-2026-03│서버  │웹서버..│  Dell  │●사용중│서버실│03-20 │  │
│ │ □ │NB-2026-041│노트북│디자인..│ Apple  │●수리중│-    │03-19 │  │
│ └───┴──────────┴──────┴───────┴────────┴──────┴──────┴──────┘  │
│                                                                 │
│ 총 156건                              < 1  2  3  4  5 ... 8 >  │
└─────────────────────────────────────────────────────────────────┘
```

- 상태별 색상 뱃지: 사용중(파랑), 여유(초록), 수리중(주황), 폐기(회색), 분실(빨강)
- 행 클릭 시 자산 상세 페이지로 이동
- 체크박스 선택 후 일괄 상태 변경 가능

### 6.2 자산 등록 폼 (`/inventories/assets/new`)

스텝 위저드 방식 (4단계):

```
┌─────────────────────────────────────────────────────────────────┐
│ 자산 등록                                                        │
│                                                                 │
│  ① 분류 선택  ──  ② 기본 정보  ──  ③ 스펙 입력  ──  ④ 이미지     │
│  [완료]          [현재]           [ ]             [ ]            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ STEP 2: 기본 정보 ─────────────────────────────────────┐   │
│  │                                                          │   │
│  │  선택된 분류: 하드웨어 > 노트북 (NB)                       │   │
│  │                                                          │   │
│  │  자산명 *        [____________________________]          │   │
│  │  제조사          [____________________________]          │   │
│  │  모델명          [____________________________]          │   │
│  │  시리얼번호      [____________________________]          │   │
│  │                                                          │   │
│  │  ── 구매 정보 ──                                         │   │
│  │  구매일          [______ 📅]                              │   │
│  │  구매처          [____________________________]          │   │
│  │  구매가격(원)    [____________________________]          │   │
│  │                                                          │   │
│  │  ── 위치 및 보증 ──                                      │   │
│  │  위치            [____________________________]          │   │
│  │  보증 만료일     [______ 📅]                              │   │
│  │                                                          │   │
│  │  비고            [____________________________]          │   │
│  │                  [____________________________]          │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│                                    [이전 단계]  [다음 단계 →]     │
└─────────────────────────────────────────────────────────────────┘
```

- **STEP 1 (분류 선택)**: 트리 구조에서 카테고리를 선택
- **STEP 2 (기본 정보)**: 자산명, 제조사, 모델 등 기본 정보 입력
- **STEP 3 (스펙 입력)**: 선택된 카테고리의 `spec_schema_json` 기반으로 동적 폼 렌더링
- **STEP 4 (이미지 업로드)**: 드래그 앤 드롭 이미지 업로드 영역, 최대 5장

### 6.3 자산 상세 페이지 (`/inventories/assets/{id}`)

```
┌─────────────────────────────────────────────────────────────────┐
│ ← 목록으로    NB-2026-042  개발팀 노트북 #42      [수정] [삭제]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [기본 정보]  [배정 현황]  [이력]                                  │
│                                                                 │
│  ┌─ 기본 정보 ─────────────────────┬─ 이미지 ────────────────┐  │
│  │ 분류      하드웨어 > 노트북      │  ┌──────────────────┐  │  │
│  │ 상태      ● 사용중               │  │                  │  │  │
│  │ 제조사    Apple                  │  │   (자산 사진)     │  │  │
│  │ 모델      MacBook Pro 16 (2025) │  │                  │  │  │
│  │ S/N      C02XXXXXXXXX           │  └──────────────────┘  │  │
│  │                                  │   1 / 3   < >         │  │
│  │ ── 스펙 ──                       │                        │  │
│  │ CPU      Apple M4 Pro           ├────────────────────────┤  │
│  │ RAM      36GB                   │ ── 구매 정보 ──        │  │
│  │ Storage  SSD 1TB                │ 구매일   2026-03-15    │  │
│  │ 화면     16.2인치                │ 구매처   (주)맥코리아   │  │
│  │ OS       macOS Sequoia          │ 구매가격 3,990,000원   │  │
│  │                                  │ 보증만료 2029-03-15    │  │
│  └──────────────────────────────────┴────────────────────────┘  │
│                                                                 │
│  ┌─ 현재 배정 ──────────────────────────────────────────────┐   │
│  │ 배정 대상: 김개발 (개발팀)                                 │   │
│  │ 배정일:   2026-03-20                    [반납 처리]       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─ 이력 타임라인 ──────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ● 2026-03-22 08:30  상태 변경                           │   │
│  │  │  사용중 → 수리중 (관리자)                              │   │
│  │  │  "화면 깜빡임 현상으로 수리 접수"                        │   │
│  │  │                                                       │   │
│  │  ● 2026-03-20 02:00  배정                                │   │
│  │  │  → 김개발 (개발팀) (관리자)                             │   │
│  │  │                                                       │   │
│  │  ● 2026-03-19 09:00  등록                                │   │
│  │     신규 자산 등록 (관리자)                                │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

- 탭 구성: 기본 정보 / 배정 현황 / 이력
- 이력은 타임라인 형식으로 시간순 표시
- 상태 변경, 배정/반납은 해당 탭에서 바로 실행 가능

---

## 7. 인수 조건

### 7.1 자산 카테고리

- [ ] 관리자가 자산 카테고리를 생성/수정/삭제할 수 있다.
- [ ] 카테고리는 최대 3단계 계층으로 구성된다.
- [ ] 하위 카테고리가 있는 카테고리는 삭제할 수 없다.
- [ ] 자산이 연결된 카테고리는 삭제할 수 없다.
- [ ] 카테고리별 스펙 스키마(JSON Schema)를 설정할 수 있다.

### 7.2 자산 등록

- [ ] 필수 항목(카테고리, 자산명)을 입력하여 자산을 등록할 수 있다.
- [ ] 자산번호가 `{카테고리코드}-{연도}-{순번}` 형식으로 자동 채번된다.
- [ ] 같은 카테고리/연도 조합에서 순번이 중복되지 않는다.
- [ ] 카테고리의 `spec_schema_json`에 따라 스펙 입력 폼이 동적으로 생성된다.
- [ ] 자산 이미지를 최대 5장 업로드할 수 있다 (JPG/PNG, 10MB 이하).
- [ ] 자산 등록 시 이력에 `REGISTERED` 액션이 자동 기록된다.
- [ ] 등록된 자산의 초기 상태는 `AVAILABLE`이다.

### 7.3 자산 조회 및 검색

- [ ] 자산 목록을 페이지네이션으로 조회할 수 있다.
- [ ] 카테고리, 상태, 위치로 필터링할 수 있다.
- [ ] 자산번호, 자산명, 제조사, 모델명, 시리얼번호로 검색할 수 있다.
- [ ] 자산 상세 페이지에서 전체 정보와 배정 현황을 확인할 수 있다.

### 7.4 자산 상태 관리

- [ ] 자산 상태를 변경할 수 있다 (`AVAILABLE` ↔ `IN_USE` ↔ `IN_REPAIR` → `DISPOSED`).
- [ ] 상태 변경 시 이력에 `STATUS_CHANGED` 액션이 자동 기록된다.
- [ ] `DISPOSED` 상태의 자산은 다른 상태로 변경할 수 없다.
- [ ] 사용중(`IN_USE`) 자산은 소프트 삭제할 수 없다.

### 7.5 자산 이력

- [ ] 자산의 모든 변경 이력을 시간순으로 조회할 수 있다.
- [ ] 이력에는 수행자, 수행 시각, 변경 전/후 값, 비고가 기록된다.
- [ ] 이력은 수정/삭제할 수 없다 (Immutable).

---

## 8. 참고사항

- 자산번호 채번 시 동시성 이슈를 방지하기 위해 PostgreSQL의 `SEQUENCE` 또는 `SELECT ... FOR UPDATE`를 사용한다.
- `spec_json` 유효성 검증은 백엔드에서 카테고리의 `spec_schema_json`을 기준으로 수행한다.
- 이미지 파일은 로컬 파일시스템(`{UPLOAD_DIR}/assets/{asset_id}/`)에 저장한다.
- 대량 자산 등록이 필요한 경우 엑셀 일괄 업로드 기능은 향후 확장으로 검토한다.
- 자산 폐기 시 관련 법규(전자제품 폐기 등)에 따른 절차가 필요할 수 있으며, 이는 운영 정책으로 별도 관리한다.
- 권한 체계는 `01-04` 권한 관리 모듈과 연동하여, 역할별 접근 권한을 다음과 같이 구분한다:
  - **자산 관리자**: 등록/수정/삭제/상태변경/카테고리 관리 전체 권한
  - **부서 관리자**: 본인 부서 자산 조회, 배정 요청
  - **일반 사용자**: 본인 배정 자산 조회만 가능
