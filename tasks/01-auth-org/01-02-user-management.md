# 01-02 사용자 관리 (User Management)

## 1. 개요

그룹웨어 시스템의 사용자를 관리한다. 관리자가 사용자를 등록, 수정, 비활성화할 수 있으며, 사용자 프로필 정보(이름, 사번, 연락처, 프로필 사진, 입사일 등)를 관리한다. 사용자 검색 및 목록 조회 기능을 포함한다.

- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)
- **의존성**: 01-01 인증 시스템

## 2. 기능 요구사항

### 2.1 사용자 등록

- 관리자가 새로운 사용자를 등록한다.
- 필수 입력: 이메일, 이름(한글), 사번, 초기 비밀번호
- 선택 입력: 연락처, 입사일, 프로필 사진
- 등록 시 `must_change_password = true`로 설정하여 초기 비밀번호 변경을 강제한다.
- 사번(`employee_number`)은 시스템 내에서 고유해야 한다.
- 이메일 중복 검사를 수행한다.

### 2.2 사용자 수정

- 관리자가 사용자 정보를 수정할 수 있다.
- 수정 가능 항목: 이름, 연락처, 입사일, 상태, 프로필 사진
- 이메일과 사번은 등록 후 변경 불가 (변경이 필요한 경우 시스템 관리자가 직접 처리)
- 관리자가 비밀번호를 초기화할 수 있다 (임시 비밀번호 설정 + `must_change_password = true`)

### 2.3 사용자 비활성화 (소프트 삭제)

- 퇴직 등의 사유로 사용자를 비활성화한다.
- `is_active = false`로 설정하고 `status = 'RESIGNED'`로 변경한다.
- 비활성화된 사용자는 로그인이 차단되며, 기존 세션(refresh token)이 모두 무효화된다.
- 비활성화된 사용자 데이터는 삭제하지 않고 보존한다 (soft delete).

### 2.4 사용자 상태 관리

- **ACTIVE (재직)**: 정상적으로 시스템을 이용할 수 있는 상태
- **ON_LEAVE (휴직)**: 휴직 중인 상태, 로그인은 가능하나 관리자 설정에 따라 제한 가능
- **RESIGNED (퇴직)**: 퇴직 처리된 상태, 로그인 차단

### 2.5 사용자 검색

- 이름(한글), 사번, 이메일로 검색할 수 있다.
- 부분 일치(LIKE) 검색을 지원한다.
- 검색 결과에 부서명과 직급을 함께 표시한다 (01-03 완료 후).

### 2.6 사용자 목록 조회

- 페이지네이션 지원 (기본 20건/페이지)
- 상태별 필터링 (전체, 재직, 휴직, 퇴직)
- 정렬: 이름순, 사번순, 입사일순
- 목록 항목: 프로필 사진(썸네일), 이름, 사번, 이메일, 부서, 직급, 상태

### 2.7 프로필 사진 관리

- 지원 형식: JPG, PNG, WebP
- 최대 파일 크기: **5MB**
- 업로드 시 자동 리사이징: 원본 보관 + 썸네일(150x150) 생성
- 기본 프로필 사진(이니셜 아바타)을 제공한다.

### 2.8 내 프로필 관리

- 사용자 본인이 자신의 프로필을 조회/수정할 수 있다.
- 수정 가능 항목: 연락처, 프로필 사진
- 이름, 사번, 이메일, 상태 등은 본인이 직접 변경할 수 없다.

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 사용자 목록 API 응답 시간 300ms 이내 (1,000명 기준) |
| 성능 | 사용자 검색 API 응답 시간 500ms 이내 |
| 보안 | 사용자 등록/수정/비활성화는 관리자 권한 필요 |
| 보안 | 비밀번호 초기화 시 이전 비밀번호를 노출하지 않음 |
| 저장소 | 프로필 사진은 로컬 파일시스템(`{UPLOAD_DIR}/profiles/`)에 저장 |
| 데이터 | 개인정보 처리 시 관련 법규(개인정보보호법) 준수 |

## 4. 데이터베이스 스키마

### 4.1 `users` 테이블 (확장)

> 01-01에서 정의한 인증 관련 컬럼에 프로필 컬럼을 추가한다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 사용자 고유 식별자 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 로그인 이메일 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 해싱된 비밀번호 |
| name | VARCHAR(50) | NOT NULL | 사용자 이름 (한글) |
| employee_number | VARCHAR(20) | UNIQUE, NOT NULL | 사번 |
| phone | VARCHAR(20) | NULL | 연락처 |
| profile_image_url | VARCHAR(500) | NULL | 프로필 사진 URL |
| profile_thumbnail_url | VARCHAR(500) | NULL | 프로필 썸네일 URL |
| hire_date | DATE | NULL | 입사일 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'ACTIVE' | 상태 (ACTIVE, ON_LEAVE, RESIGNED) |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | 계정 활성화 여부 |
| must_change_password | BOOLEAN | NOT NULL, DEFAULT false | 초기 비밀번호 변경 필요 여부 |
| failed_login_count | INTEGER | NOT NULL, DEFAULT 0 | 연속 로그인 실패 횟수 |
| locked_until | TIMESTAMPTZ | NULL | 계정 잠금 해제 시각 (UTC) |
| last_login_at | TIMESTAMPTZ | NULL | 마지막 로그인 시각 (UTC) |
| created_by | UUID | FK → users.id, NULL | 생성자 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |
| updated_by | UUID | FK → users.id, NULL | 수정자 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 수정 시각 (UTC) |
| deleted_at | TIMESTAMPTZ | NULL | 소프트 삭제 시각 (UTC) |

**인덱스:**
- `idx_users_email` — UNIQUE INDEX ON email WHERE deleted_at IS NULL
- `idx_users_employee_number` — UNIQUE INDEX ON employee_number WHERE deleted_at IS NULL
- `idx_users_name` — INDEX ON name (검색용)
- `idx_users_status` — INDEX ON status
- `idx_users_deleted_at` — INDEX ON deleted_at

**CHECK 제약조건:**
- `chk_users_status` — status IN ('ACTIVE', 'ON_LEAVE', 'RESIGNED')

## 5. API 명세

### 5.1 GET /api/v1/users

사용자 목록을 조회한다.

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| page | integer | N | 1 | 페이지 번호 |
| size | integer | N | 20 | 페이지당 항목 수 (최대 100) |
| status | string | N | - | 상태 필터 (ACTIVE, ON_LEAVE, RESIGNED) |
| sort_by | string | N | name | 정렬 기준 (name, employee_number, hire_date) |
| sort_order | string | N | asc | 정렬 순서 (asc, desc) |

**Response 200:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "hong@company.com",
      "name": "홍길동",
      "employee_number": "EMP-2024-001",
      "phone": "010-1234-5678",
      "profile_thumbnail_url": "https://storage.example.com/thumbs/user1.jpg",
      "hire_date": "2024-03-01",
      "status": "ACTIVE",
      "department_name": "개발팀",
      "position_name": "과장",
      "created_at": "2024-03-01T00:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20,
  "total_pages": 8
}
```

### 5.2 POST /api/v1/users

새 사용자를 등록한다. (관리자 전용)

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "email": "kim@company.com",
  "name": "김철수",
  "employee_number": "EMP-2024-010",
  "password": "TempP@ss1!",
  "phone": "010-9876-5432",
  "hire_date": "2024-06-01"
}
```

**Response 201:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "email": "kim@company.com",
  "name": "김철수",
  "employee_number": "EMP-2024-010",
  "phone": "010-9876-5432",
  "hire_date": "2024-06-01",
  "status": "ACTIVE",
  "must_change_password": true,
  "created_at": "2026-03-23T09:00:00Z"
}
```

**Response 409:**
```json
{
  "detail": "이미 등록된 이메일입니다."
}
```

### 5.3 GET /api/v1/users/{id}

특정 사용자의 상세 정보를 조회한다.

**Headers:** `Authorization: Bearer {access_token}`

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "hong@company.com",
  "name": "홍길동",
  "employee_number": "EMP-2024-001",
  "phone": "010-1234-5678",
  "profile_image_url": "https://storage.example.com/profiles/user1.jpg",
  "profile_thumbnail_url": "https://storage.example.com/thumbs/user1.jpg",
  "hire_date": "2024-03-01",
  "status": "ACTIVE",
  "is_active": true,
  "last_login_at": "2026-03-23T08:30:00Z",
  "departments": [
    {
      "department_id": "...",
      "department_name": "개발팀",
      "position_name": "과장",
      "title_name": "팀장",
      "is_primary": true
    }
  ],
  "created_at": "2024-03-01T00:00:00Z",
  "updated_at": "2026-03-20T14:00:00Z"
}
```

**Response 404:**
```json
{
  "detail": "사용자를 찾을 수 없습니다."
}
```

### 5.4 PUT /api/v1/users/{id}

사용자 정보를 수정한다. (관리자 전용)

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "name": "홍길동",
  "phone": "010-1111-2222",
  "hire_date": "2024-03-01",
  "status": "ON_LEAVE"
}
```

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "hong@company.com",
  "name": "홍길동",
  "phone": "010-1111-2222",
  "hire_date": "2024-03-01",
  "status": "ON_LEAVE",
  "updated_at": "2026-03-23T10:00:00Z"
}
```

### 5.5 DELETE /api/v1/users/{id}

사용자를 비활성화한다 (소프트 삭제). (관리자 전용)

**Headers:** `Authorization: Bearer {access_token}`

**Response 200:**
```json
{
  "message": "사용자가 비활성화되었습니다."
}
```

### 5.6 GET /api/v1/users/search

사용자를 검색한다.

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| q | string | Y | - | 검색어 (이름, 사번, 이메일) |
| status | string | N | ACTIVE | 상태 필터 |
| limit | integer | N | 10 | 최대 결과 수 (최대 50) |

**Response 200:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "홍길동",
      "employee_number": "EMP-2024-001",
      "email": "hong@company.com",
      "profile_thumbnail_url": "https://storage.example.com/thumbs/user1.jpg",
      "department_name": "개발팀",
      "position_name": "과장"
    }
  ],
  "total": 1
}
```

### 5.7 PUT /api/v1/users/{id}/profile-image

프로필 사진을 업로드한다.

**Headers:** `Authorization: Bearer {access_token}`, `Content-Type: multipart/form-data`

**Request:** `file` — 이미지 파일 (JPG, PNG, WebP, 최대 5MB)

**Response 200:**
```json
{
  "profile_image_url": "https://storage.example.com/profiles/user1_20260323.jpg",
  "profile_thumbnail_url": "https://storage.example.com/thumbs/user1_20260323.jpg"
}
```

**Response 400:**
```json
{
  "detail": "지원하지 않는 파일 형식입니다. JPG, PNG, WebP만 허용됩니다."
}
```

**Response 413:**
```json
{
  "detail": "파일 크기가 5MB를 초과합니다."
}
```

### 5.8 PUT /api/v1/users/{id}/reset-password

관리자가 사용자 비밀번호를 초기화한다. (관리자 전용)

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "new_password": "TempP@ss1!"
}
```

**Response 200:**
```json
{
  "message": "비밀번호가 초기화되었습니다. 사용자는 다음 로그인 시 비밀번호를 변경해야 합니다."
}
```

### 5.9 GET /api/v1/users/me

현재 로그인한 사용자의 프로필을 조회한다.

**Headers:** `Authorization: Bearer {access_token}`

**Response 200:** — 5.3과 동일한 구조

### 5.10 PUT /api/v1/users/me

현재 로그인한 사용자의 프로필을 수정한다.

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "phone": "010-9999-8888"
}
```

**Response 200:** — 수정된 사용자 정보

## 6. 화면 설계

### 6.1 사용자 목록 페이지 (`/admin/users`)

```
┌──────────────────────────────────────────────────────────┐
│ 사용자 관리                                  [+ 사용자 등록] │
├──────────────────────────────────────────────────────────┤
│ [전체] [재직] [휴직] [퇴직]       검색어 입력...            │
├──────────────────────────────────────────────────────────┤
│  사진  │  이름    │  사번          │  이메일           │ ...│
│────────┼──────────┼────────────────┼───────────────────┼────│
│  [사진]│ 홍길동   │ EMP-2024-001  │ hong@company.com  │ ...│
│  [사진]│ 김철수   │ EMP-2024-002  │ kim@company.com   │ ...│
│  [사진]│ 이영희   │ EMP-2024-003  │ lee@company.com   │ ...│
├──────────────────────────────────────────────────────────┤
│              ← 1  2  3  4  5  →              총 150명    │
└──────────────────────────────────────────────────────────┘
```

- 상단: 제목 + 사용자 등록 버튼
- 필터 탭: 상태별 필터링 (전체/재직/휴직/퇴직), 각 탭에 해당 인원수 배지 표시
- 검색 입력: 이름, 사번, 이메일로 즉시 검색 (디바운싱 300ms)
- 테이블 헤더: 클릭하여 정렬 변경
- 각 행: 클릭 시 사용자 상세 페이지로 이동
- 하단: 페이지네이션 컨트롤

### 6.2 사용자 등록/편집 폼 (모달 또는 별도 페이지)

```
┌──────────────────────────────────────────┐
│ 사용자 등록                               │
├──────────────────────────────────────────┤
│                                          │
│  이메일 *      [                        ]│
│  이름 *        [                        ]│
│  사번 *        [                        ]│
│  초기 비밀번호 * [                       ]│
│  연락처        [                        ]│
│  입사일        [     날짜 선택          ]│
│  프로필 사진    [파일 선택]               │
│                                          │
│            [취소]  [등록]                 │
└──────────────────────────────────────────┘
```

- 필수 필드에 * 표시
- 이메일 필드: 실시간 중복 검사 (입력 완료 후 API 호출)
- 사번 필드: 실시간 중복 검사
- 입사일 필드: 달력 위젯 (date picker)
- 프로필 사진: 파일 선택 후 미리보기 표시
- 수정 모드에서는 이메일/사번 필드가 비활성화

### 6.3 사용자 상세 페이지 (`/admin/users/{id}`)

```
┌──────────────────────────────────────────────────────────┐
│ ← 사용자 목록                                             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────┐   홍길동                                        │
│  │ 사진  │   개발팀 / 과장 / 팀장                          │
│  └──────┘   hong@company.com                             │
│             상태: 재직                                     │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ [기본 정보]  [소속 정보]  [활동 이력]                       │
├──────────────────────────────────────────────────────────┤
│  사번         EMP-2024-001                                │
│  연락처       010-1234-5678                               │
│  입사일       2024-03-01                                  │
│  최종 로그인   2026-03-23 08:30                            │
│                                                          │
│  [수정]  [비밀번호 초기화]  [비활성화]                      │
└──────────────────────────────────────────────────────────┘
```

- 상단: 프로필 요약 (사진, 이름, 소속, 이메일, 상태)
- 탭 구성: 기본 정보 / 소속 정보 (01-03 연동) / 활동 이력
- 하단 액션 버튼: 수정, 비밀번호 초기화, 비활성화

### 6.4 내 프로필 페이지 (`/profile`)

```
┌──────────────────────────────────────────────────────────┐
│ 내 프로필                                                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────┐   홍길동                                        │
│  │ 사진  │   [사진 변경]                                   │
│  └──────┘                                                │
│                                                          │
│  이메일       hong@company.com                            │
│  사번         EMP-2024-001                                │
│  소속         개발팀 / 과장 / 팀장                          │
│  연락처       [010-1234-5678      ] ← 수정 가능            │
│  입사일       2024-03-01                                  │
│                                                          │
│  [비밀번호 변경]  [저장]                                   │
└──────────────────────────────────────────────────────────┘
```

- 본인이 수정할 수 있는 항목만 입력 가능 (연락처, 프로필 사진)
- 읽기 전용 항목은 회색 텍스트로 표시
- 비밀번호 변경 버튼 클릭 시 비밀번호 변경 모달 열림

## 7. 인수 조건

### 7.1 사용자 등록

- [ ] 관리자가 필수 정보(이메일, 이름, 사번, 비밀번호)를 입력하여 사용자를 등록할 수 있다.
- [ ] 등록된 사용자의 `must_change_password`가 true로 설정된다.
- [ ] 중복 이메일로 등록 시 409 에러가 반환된다.
- [ ] 중복 사번으로 등록 시 409 에러가 반환된다.
- [ ] 관리자가 아닌 사용자가 등록 시도 시 403 에러가 반환된다.

### 7.2 사용자 수정

- [ ] 관리자가 사용자의 이름, 연락처, 입사일, 상태를 수정할 수 있다.
- [ ] 이메일과 사번은 수정할 수 없다.
- [ ] 수정 시 `updated_by`와 `updated_at`이 갱신된다.

### 7.3 사용자 비활성화

- [ ] 관리자가 사용자를 비활성화할 수 있다.
- [ ] 비활성화 시 `is_active = false`, `status = 'RESIGNED'`, `deleted_at`이 설정된다.
- [ ] 비활성화된 사용자의 모든 refresh token이 무효화된다.
- [ ] 비활성화된 사용자는 목록에서 퇴직 필터로만 조회 가능하다.

### 7.4 사용자 검색

- [ ] 이름으로 부분 일치 검색이 가능하다.
- [ ] 사번으로 부분 일치 검색이 가능하다.
- [ ] 이메일로 부분 일치 검색이 가능하다.
- [ ] 검색 결과에 부서명과 직급이 표시된다.

### 7.5 목록 조회

- [ ] 페이지네이션이 올바르게 동작한다 (total, page, size, total_pages).
- [ ] 상태별 필터링이 올바르게 동작한다.
- [ ] 이름순, 사번순, 입사일순 정렬이 동작한다.

### 7.6 프로필 사진

- [ ] JPG, PNG, WebP 이미지를 업로드할 수 있다.
- [ ] 5MB 초과 파일은 업로드가 거부된다.
- [ ] 업로드 시 원본과 썸네일(150x150)이 생성된다.
- [ ] 프로필 사진이 없는 사용자에게 기본 아바타가 표시된다.

### 7.7 내 프로필

- [ ] 로그인한 사용자가 자신의 프로필을 조회할 수 있다.
- [ ] 연락처와 프로필 사진을 수정할 수 있다.
- [ ] 이름, 사번, 이메일 등은 수정할 수 없다.

## 8. 참고사항

- 프로필 사진은 로컬 파일시스템(`{UPLOAD_DIR}/profiles/{user_id}/`)에 저장한다.
- 프로필 사진 조회는 서버 경유 API (`/api/v1/users/{id}/profile-image`)로 제공한다.
- 사용자 목록 API의 `department_name`, `position_name`은 01-03(조직도) 모듈 완료 후 JOIN으로 제공한다. 01-03 미완료 시 해당 필드는 null을 반환한다.
- 사용자 검색은 PostgreSQL의 `ILIKE`를 사용하되, 대규모 데이터 시 Full-Text Search(tsvector/tsquery) 또는 별도 검색 엔진(Elasticsearch) 도입을 검토한다.
- CSV 일괄 등록 기능은 추후 별도 태스크로 진행한다.
- 개인정보 처리 시 마스킹(연락처 중간 4자리 등)을 적용하여 API 응답에 포함한다 (권한에 따라 분기).
