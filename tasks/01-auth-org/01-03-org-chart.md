# 01-03 조직도 (Organization Chart)

## 1. 개요

그룹웨어 시스템의 조직 구조를 관리한다. 부서의 계층 구조(트리형), 직급, 직책을 정의하고, 사용자를 부서에 배정하는 기능을 제공한다. 주 소속 외에 겸직을 지원하며, 조직도를 시각적으로 조회할 수 있는 트리 뷰를 제공한다.

- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)
- **의존성**: 01-02 사용자 관리

## 2. 기능 요구사항

### 2.1 부서 관리

- 부서의 계층 구조를 트리 형태로 관리한다 (`parent_id`를 이용한 self-reference).
- 부서 CRUD: 생성, 조회, 수정, 비활성화(소프트 삭제)
- 부서 속성: 부서명, 부서 코드, 상위 부서, 정렬 순서, 레벨(depth)
- 부서 코드는 시스템 내 고유해야 한다.
- 하위 부서가 존재하는 부서는 삭제(비활성화)할 수 없다 (하위 부서를 먼저 이동 또는 삭제해야 함).
- 부서 이동: 상위 부서를 변경하여 조직 구조를 재편할 수 있다.
- 부서 이동 시 순환 참조가 발생하지 않도록 검증한다.

### 2.2 직급 관리

직급은 조직 내 서열을 나타내는 체계이다.

| 레벨 | 직급명 |
|------|--------|
| 1 | 사원 |
| 2 | 대리 |
| 3 | 과장 |
| 4 | 차장 |
| 5 | 부장 |
| 6 | 이사 |
| 7 | 상무 |
| 8 | 전무 |
| 9 | 부사장 |
| 10 | 사장 |

- 직급 CRUD (시스템 관리자만 가능)
- 각 직급에 레벨(숫자)을 부여하여 서열을 관리한다.
- 정렬 순서(`sort_order`)로 표시 순서를 제어한다.

### 2.3 직책 관리

직책은 조직 내 역할(보직)을 나타내는 체계이다.

| 레벨 | 직책명 |
|------|--------|
| 1 | 팀원 |
| 2 | 파트장 |
| 3 | 팀장 |
| 4 | 실장 |
| 5 | 본부장 |
| 6 | 대표이사 |

- 직책 CRUD (시스템 관리자만 가능)
- 각 직책에 레벨(숫자)을 부여하여 서열을 관리한다.
- 직책은 부서 내에서의 역할을 나타내므로, 같은 사용자가 다른 부서에서 다른 직책을 가질 수 있다.

### 2.4 사용자-부서 배정

- 사용자를 부서에 배정한다 (직급, 직책 포함).
- **주 소속(`is_primary = true`)**: 반드시 1개, 필수
- **겸직(`is_primary = false`)**: 0개 이상 가능
- 배정 이력을 관리한다 (`start_date`, `end_date`).
- 동일 부서에 동일 사용자를 중복 배정할 수 없다 (활성 배정 기준).
- 부서 이동 시 기존 배정의 `end_date`를 설정하고 새 배정을 생성한다.

### 2.5 조직도 시각화

- 전체 조직도를 트리 뷰로 표시한다.
- 부서 → 하위 부서 → 소속 인원 구조로 표시한다.
- 각 인원은 이름, 직급, 직책, 프로필 사진 썸네일을 표시한다.
- 부서 노드를 펼치기/접기 할 수 있다.
- 특정 부서를 선택하면 해당 부서의 상세 정보와 소속 인원 목록을 표시한다.
- 사용자 이름으로 조직도 내 검색이 가능하며, 검색 결과 해당 노드를 하이라이트한다.

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 전체 조직도 트리 API 응답 시간 500ms 이내 (부서 100개, 사용자 1,000명 기준) |
| 성능 | 부서 계층 조회 시 재귀 쿼리(WITH RECURSIVE) 활용 |
| 무결성 | 부서 이동 시 순환 참조 방지 검증 필수 |
| 무결성 | 주 소속은 반드시 1개만 존재하도록 비즈니스 로직에서 보장 |
| UX | 조직도 트리 뷰에서 드래그 앤 드롭으로 부서 이동 지원 (향후 확장) |
| 캐싱 | 조직도 트리는 변경이 드물므로 캐싱 적용 검토 (Redis, 5분 TTL) |

## 4. 데이터베이스 스키마

### 4.1 `departments` 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 부서 고유 식별자 |
| name | VARCHAR(100) | NOT NULL | 부서명 |
| code | VARCHAR(50) | UNIQUE, NOT NULL | 부서 코드 |
| parent_id | UUID | FK → departments.id, NULL | 상위 부서 (NULL이면 최상위) |
| level | INTEGER | NOT NULL, DEFAULT 1 | 계층 깊이 (1부터 시작) |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | 동일 레벨 내 정렬 순서 |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | 활성화 여부 |
| created_by | UUID | FK → users.id, NULL | 생성자 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |
| updated_by | UUID | FK → users.id, NULL | 수정자 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 수정 시각 (UTC) |
| deleted_at | TIMESTAMPTZ | NULL | 소프트 삭제 시각 (UTC) |

**인덱스:**
- `idx_departments_code` — UNIQUE INDEX ON code WHERE deleted_at IS NULL
- `idx_departments_parent_id` — INDEX ON parent_id
- `idx_departments_level` — INDEX ON level
- `idx_departments_deleted_at` — INDEX ON deleted_at

### 4.2 `positions` 테이블 (직급)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 직급 고유 식별자 |
| name | VARCHAR(50) | NOT NULL | 직급명 (사원, 대리, 과장 등) |
| level | INTEGER | UNIQUE, NOT NULL | 직급 레벨 (숫자가 클수록 상위) |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | 표시 정렬 순서 |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | 활성화 여부 |
| created_by | UUID | FK → users.id, NULL | 생성자 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |
| updated_by | UUID | FK → users.id, NULL | 수정자 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 수정 시각 (UTC) |
| deleted_at | TIMESTAMPTZ | NULL | 소프트 삭제 시각 (UTC) |

**인덱스:**
- `idx_positions_level` — UNIQUE INDEX ON level WHERE deleted_at IS NULL
- `idx_positions_deleted_at` — INDEX ON deleted_at

### 4.3 `titles` 테이블 (직책)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 직책 고유 식별자 |
| name | VARCHAR(50) | NOT NULL | 직책명 (팀원, 팀장, 실장 등) |
| level | INTEGER | UNIQUE, NOT NULL | 직책 레벨 (숫자가 클수록 상위) |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | 표시 정렬 순서 |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | 활성화 여부 |
| created_by | UUID | FK → users.id, NULL | 생성자 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |
| updated_by | UUID | FK → users.id, NULL | 수정자 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 수정 시각 (UTC) |
| deleted_at | TIMESTAMPTZ | NULL | 소프트 삭제 시각 (UTC) |

**인덱스:**
- `idx_titles_level` — UNIQUE INDEX ON level WHERE deleted_at IS NULL
- `idx_titles_deleted_at` — INDEX ON deleted_at

### 4.4 `user_departments` 테이블 (사용자-부서 배정)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 배정 고유 식별자 |
| user_id | UUID | FK → users.id, NOT NULL | 사용자 참조 |
| department_id | UUID | FK → departments.id, NOT NULL | 부서 참조 |
| position_id | UUID | FK → positions.id, NULL | 직급 참조 |
| title_id | UUID | FK → titles.id, NULL | 직책 참조 |
| is_primary | BOOLEAN | NOT NULL, DEFAULT false | 주 소속 여부 |
| start_date | DATE | NOT NULL | 배정 시작일 |
| end_date | DATE | NULL | 배정 종료일 (NULL이면 현재 활성) |
| created_by | UUID | FK → users.id, NULL | 생성자 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |
| updated_by | UUID | FK → users.id, NULL | 수정자 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 수정 시각 (UTC) |
| deleted_at | TIMESTAMPTZ | NULL | 소프트 삭제 시각 (UTC) |

**인덱스:**
- `idx_user_departments_user_id` — INDEX ON user_id
- `idx_user_departments_department_id` — INDEX ON department_id
- `idx_user_departments_active` — INDEX ON (user_id, department_id) WHERE end_date IS NULL AND deleted_at IS NULL
- `idx_user_departments_primary` — UNIQUE INDEX ON user_id WHERE is_primary = true AND end_date IS NULL AND deleted_at IS NULL

**제약조건:**
- 동일 사용자의 동일 부서 활성 배정 중복 방지 (partial unique index)
- 사용자당 활성 주 소속은 1개만 허용 (partial unique index)

## 5. API 명세

### 5.1 부서 API

#### GET /api/v1/departments

부서 목록을 조회한다 (플랫 리스트).

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| parent_id | UUID | N | - | 특정 상위 부서의 하위 부서만 조회 |
| include_inactive | boolean | N | false | 비활성 부서 포함 여부 |

**Response 200:**
```json
{
  "items": [
    {
      "id": "...",
      "name": "경영지원본부",
      "code": "DEPT-001",
      "parent_id": null,
      "level": 1,
      "sort_order": 1,
      "is_active": true,
      "member_count": 5,
      "children_count": 3
    }
  ]
}
```

#### POST /api/v1/departments

부서를 생성한다. (관리자 전용)

**Request Body:**
```json
{
  "name": "프론트엔드팀",
  "code": "DEPT-001-002",
  "parent_id": "상위부서-uuid",
  "sort_order": 2
}
```

**Response 201:**
```json
{
  "id": "...",
  "name": "프론트엔드팀",
  "code": "DEPT-001-002",
  "parent_id": "상위부서-uuid",
  "level": 3,
  "sort_order": 2,
  "is_active": true,
  "created_at": "2026-03-23T09:00:00Z"
}
```

**Response 409:**
```json
{
  "detail": "이미 존재하는 부서 코드입니다."
}
```

#### GET /api/v1/departments/{id}

부서 상세 정보를 조회한다.

**Response 200:**
```json
{
  "id": "...",
  "name": "프론트엔드팀",
  "code": "DEPT-001-002",
  "parent_id": "상위부서-uuid",
  "parent_name": "개발실",
  "level": 3,
  "sort_order": 2,
  "is_active": true,
  "member_count": 8,
  "members": [
    {
      "user_id": "...",
      "name": "홍길동",
      "employee_number": "EMP-2024-001",
      "position_name": "과장",
      "title_name": "팀장",
      "is_primary": true,
      "profile_thumbnail_url": "..."
    }
  ],
  "children": [
    {
      "id": "...",
      "name": "UI파트",
      "code": "DEPT-001-002-001",
      "member_count": 3
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2026-03-20T14:00:00Z"
}
```

#### PUT /api/v1/departments/{id}

부서 정보를 수정한다. (관리자 전용)

**Request Body:**
```json
{
  "name": "프론트엔드개발팀",
  "parent_id": "새-상위부서-uuid",
  "sort_order": 3
}
```

**Response 200:** — 수정된 부서 정보

**Response 400:**
```json
{
  "detail": "순환 참조가 발생합니다. 하위 부서를 상위 부서로 지정할 수 없습니다."
}
```

#### DELETE /api/v1/departments/{id}

부서를 비활성화한다. (관리자 전용)

**Response 200:**
```json
{
  "message": "부서가 비활성화되었습니다."
}
```

**Response 400:**
```json
{
  "detail": "하위 부서가 존재합니다. 하위 부서를 먼저 이동하거나 삭제해주세요."
}
```

### 5.2 직급 API

#### GET /api/v1/positions

직급 목록을 조회한다.

**Response 200:**
```json
{
  "items": [
    { "id": "...", "name": "사원", "level": 1, "sort_order": 1 },
    { "id": "...", "name": "대리", "level": 2, "sort_order": 2 },
    { "id": "...", "name": "과장", "level": 3, "sort_order": 3 }
  ]
}
```

#### POST /api/v1/positions

직급을 생성한다. (시스템 관리자 전용)

**Request Body:**
```json
{
  "name": "수석",
  "level": 6,
  "sort_order": 6
}
```

#### PUT /api/v1/positions/{id}

직급을 수정한다. (시스템 관리자 전용)

#### DELETE /api/v1/positions/{id}

직급을 비활성화한다. (시스템 관리자 전용)

> 해당 직급에 배정된 사용자가 있으면 삭제 불가

### 5.3 직책 API

#### GET /api/v1/titles

직책 목록을 조회한다.

**Response 200:**
```json
{
  "items": [
    { "id": "...", "name": "팀원", "level": 1, "sort_order": 1 },
    { "id": "...", "name": "파트장", "level": 2, "sort_order": 2 },
    { "id": "...", "name": "팀장", "level": 3, "sort_order": 3 }
  ]
}
```

#### POST /api/v1/titles

직책을 생성한다. (시스템 관리자 전용)

#### PUT /api/v1/titles/{id}

직책을 수정한다. (시스템 관리자 전용)

#### DELETE /api/v1/titles/{id}

직책을 비활성화한다. (시스템 관리자 전용)

> 해당 직책에 배정된 사용자가 있으면 삭제 불가

### 5.4 조직도 트리 API

#### GET /api/v1/org-chart

전체 조직도를 트리 구조로 조회한다.

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| department_id | UUID | N | - | 특정 부서를 루트로 하는 서브 트리 조회 |
| include_members | boolean | N | true | 소속 인원 포함 여부 |

**Response 200:**
```json
{
  "tree": [
    {
      "id": "...",
      "name": "대표이사실",
      "code": "DEPT-CEO",
      "level": 1,
      "members": [
        {
          "user_id": "...",
          "name": "박사장",
          "position_name": "사장",
          "title_name": "대표이사",
          "profile_thumbnail_url": "...",
          "is_primary": true
        }
      ],
      "children": [
        {
          "id": "...",
          "name": "경영지원본부",
          "code": "DEPT-001",
          "level": 2,
          "members": [...],
          "children": [
            {
              "id": "...",
              "name": "인사팀",
              "code": "DEPT-001-001",
              "level": 3,
              "members": [...],
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

### 5.5 사용자 부서 배정 API

#### POST /api/v1/users/{id}/departments

사용자를 부서에 배정한다. (관리자 전용)

**Request Body:**
```json
{
  "department_id": "부서-uuid",
  "position_id": "직급-uuid",
  "title_id": "직책-uuid",
  "is_primary": true,
  "start_date": "2026-04-01"
}
```

**Response 201:**
```json
{
  "id": "배정-uuid",
  "user_id": "...",
  "department_id": "...",
  "department_name": "개발팀",
  "position_id": "...",
  "position_name": "과장",
  "title_id": "...",
  "title_name": "팀장",
  "is_primary": true,
  "start_date": "2026-04-01",
  "end_date": null
}
```

**Response 409:**
```json
{
  "detail": "해당 부서에 이미 활성 배정이 존재합니다."
}
```

#### GET /api/v1/users/{id}/departments

사용자의 부서 배정 목록을 조회한다.

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| include_history | boolean | N | false | 종료된 배정 이력 포함 여부 |

**Response 200:**
```json
{
  "items": [
    {
      "id": "...",
      "department_id": "...",
      "department_name": "개발팀",
      "position_name": "과장",
      "title_name": "팀장",
      "is_primary": true,
      "start_date": "2024-03-01",
      "end_date": null
    },
    {
      "id": "...",
      "department_id": "...",
      "department_name": "기획팀",
      "position_name": "과장",
      "title_name": "팀원",
      "is_primary": false,
      "start_date": "2025-01-01",
      "end_date": null
    }
  ]
}
```

#### PUT /api/v1/users/{id}/departments/{assignment_id}

사용자의 부서 배정 정보를 수정한다. (관리자 전용)

**Request Body:**
```json
{
  "position_id": "새-직급-uuid",
  "title_id": "새-직책-uuid",
  "is_primary": true
}
```

#### DELETE /api/v1/users/{id}/departments/{assignment_id}

부서 배정을 종료한다 (관리자 전용). `end_date`를 현재 날짜로 설정한다.

## 6. 화면 설계

### 6.1 조직도 트리 뷰 페이지 (`/org-chart`)

```
┌──────────────────────────────────────────────────────────────┐
│ 조직도                                 🔍 이름으로 검색...    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ▼ 대표이사실                                                │
│    └ 박사장 (사장/대표이사)                                   │
│                                                              │
│  ▼ 경영지원본부                                              │
│    ├ 김본부장 (부장/본부장)                                   │
│    │                                                         │
│    ├▼ 인사팀                                                 │
│    │  ├ 이팀장 (차장/팀장)                                    │
│    │  ├ 박대리 (대리/팀원)                                    │
│    │  └ 최사원 (사원/팀원)                                    │
│    │                                                         │
│    ├▶ 총무팀                                                 │
│    └▶ 재무팀                                                 │
│                                                              │
│  ▼ 기술본부                                                  │
│    ├▼ 개발실                                                 │
│    │  ├▼ 백엔드팀                                            │
│    │  │  ├ 홍길동 (과장/팀장)                                 │
│    │  │  ├ 김개발 (대리/팀원)                                 │
│    │  │  └ ...                                               │
│    │  └▼ 프론트엔드팀                                        │
│    │     └ ...                                               │
│    └▶ QA실                                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 트리 노드: 부서명 앞에 펼치기/접기 토글 아이콘 (▼ 펼침, ▶ 접힘)
- 인원 표시: 프로필 썸네일 + 이름 + (직급/직책)
- 부서 클릭 시 우측 또는 하단에 부서 상세 패널 표시
- 인원 클릭 시 사용자 상세 정보 팝오버 또는 상세 페이지로 이동
- 검색 시 일치하는 사용자의 트리 경로를 자동으로 펼치고 하이라이트

### 6.2 부서 관리 페이지 (`/admin/departments`)

```
┌──────────────────────────────────────────────────────────────┐
│ 부서 관리                                      [+ 부서 추가] │
├────────────────────────┬─────────────────────────────────────┤
│                        │                                     │
│  ▼ 경영지원본부         │  부서 상세                          │
│    ├ 인사팀             │                                     │
│    ├ 총무팀             │  부서명: 인사팀                      │
│    └ 재무팀             │  부서 코드: DEPT-001-001             │
│  ▼ 기술본부             │  상위 부서: 경영지원본부              │
│    ├▼ 개발실            │  레벨: 3                             │
│    │  ├ 백엔드팀        │  소속 인원: 5명                      │
│    │  └ 프론트엔드팀     │                                     │
│    └ QA실              │  [수정]  [삭제]                       │
│                        │                                     │
├────────────────────────┴─────────────────────────────────────┤
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 좌측: 부서 트리 뷰 (선택 가능)
- 우측: 선택된 부서의 상세 정보
- 부서 추가 시 모달 팝업 (부서명, 부서 코드, 상위 부서 선택)
- 수정 버튼: 인라인 편집 또는 모달
- 삭제 버튼: 하위 부서 존재 시 비활성화, 확인 다이얼로그 표시

### 6.3 인사 배정 폼 (모달)

```
┌──────────────────────────────────────────┐
│ 부서 배정 - 홍길동                        │
├──────────────────────────────────────────┤
│                                          │
│  부서 *       [▼ 부서 선택 (트리형)     ]│
│  직급 *       [▼ 과장                   ]│
│  직책         [▼ 팀장                   ]│
│  주 소속      [✓]                        │
│  시작일 *     [2026-04-01  📅           ]│
│                                          │
│            [취소]  [배정]                 │
└──────────────────────────────────────────┘
```

- 부서 선택: 트리형 드롭다운 (계층 구조 표시)
- 직급 선택: 드롭다운
- 직책 선택: 드롭다운 (선택 사항)
- 주 소속 체크: 체크 시 기존 주 소속 배정의 `is_primary`를 자동으로 false로 변경할 것인지 확인

## 7. 인수 조건

### 7.1 부서 관리

- [ ] 부서를 생성할 수 있다 (부서명, 코드, 상위 부서).
- [ ] 부서 코드가 중복될 경우 409 에러가 반환된다.
- [ ] 부서를 수정할 수 있다 (부서명, 상위 부서, 정렬 순서).
- [ ] 부서 이동 시 순환 참조가 감지되면 400 에러가 반환된다.
- [ ] 하위 부서가 존재하는 부서를 삭제하면 400 에러가 반환된다.
- [ ] 부서를 비활성화하면 `is_active = false`, `deleted_at`이 설정된다.

### 7.2 직급/직책 관리

- [ ] 직급을 CRUD할 수 있다.
- [ ] 직책을 CRUD할 수 있다.
- [ ] 배정된 사용자가 있는 직급/직책은 삭제할 수 없다.

### 7.3 사용자-부서 배정

- [ ] 사용자를 부서에 배정할 수 있다 (직급, 직책, 주 소속 여부 포함).
- [ ] 주 소속은 사용자당 1개만 활성 상태로 유지된다.
- [ ] 겸직을 추가할 수 있다 (`is_primary = false`).
- [ ] 동일 부서에 중복 활성 배정 시 409 에러가 반환된다.
- [ ] 배정을 종료하면 `end_date`가 설정된다.
- [ ] 배정 이력을 조회할 수 있다.

### 7.4 조직도 시각화

- [ ] 전체 조직도가 트리 구조로 표시된다.
- [ ] 부서 노드를 펼치기/접기 할 수 있다.
- [ ] 소속 인원이 이름, 직급, 직책과 함께 표시된다.
- [ ] 이름으로 검색하면 해당 사용자의 트리 경로가 펼쳐지고 하이라이트된다.
- [ ] 특정 부서 선택 시 해당 부서의 상세 정보가 표시된다.

## 8. 참고사항

- 부서 계층 조회 시 PostgreSQL의 `WITH RECURSIVE` CTE를 활용한다.
- 조직도 트리 API 응답은 서버 사이드에서 트리 구조로 조립하여 반환한다 (프론트엔드에서 플랫 리스트를 트리로 변환하는 방식도 가능하나, 서버 사이드 조립을 권장).
- 부서 이동(parent_id 변경) 시 `level` 값을 재계산해야 한다 (해당 부서와 모든 하위 부서).
- 순환 참조 검증: 이동 대상 부서의 모든 자손 부서 목록에 새 parent_id가 포함되어 있지 않은지 확인한다.
- 조직도는 변경 빈도가 낮으므로 Redis 캐싱을 적용하되, 부서/배정 변경 시 캐시를 무효화한다.
- 프론트엔드 트리 컴포넌트는 가상화(virtualization)를 적용하여 대규모 조직에서도 성능을 보장한다.
- 겸직자는 조직도에서 겸직 부서에도 표시되며, 겸직 표시(예: [겸])를 별도로 표기한다.
