# 01-04 역할 및 권한 관리 (RBAC)

## 1. 개요

역할 기반 접근 제어(Role-Based Access Control, RBAC) 시스템을 구축한다. 역할(Role)에 권한(Permission)을 매핑하고, 사용자에게 역할을 부여하여 시스템 전반의 접근 제어를 관리한다. 프론트엔드 라우트 가드와 백엔드 미들웨어를 통해 메뉴 및 기능별 접근을 통제한다.

- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)
- **의존성**: 01-02 사용자 관리

## 2. 기능 요구사항

### 2.1 역할 관리

#### 기본 역할 (시스템 역할)

| 역할 코드 | 역할명 | 설명 |
|-----------|--------|------|
| SYSTEM_ADMIN | 시스템 관리자 | 모든 권한을 보유, 시스템 설정 및 전체 사용자/조직 관리 |
| DEPT_ADMIN | 부서 관리자 | 소속 부서 내 사용자 관리, 부서 설정 관리 |
| USER | 일반 사용자 | 기본 기능 사용 (본인 프로필, 그룹웨어 일반 기능) |

- 기본 역할은 시스템에 내장되어 있으며 삭제할 수 없다 (`is_system = true`).
- 기본 역할의 이름과 코드는 변경할 수 없다.
- 기본 역할의 권한 매핑은 변경할 수 있다.
- 관리자가 커스텀 역할을 추가로 생성할 수 있다 (`is_system = false`).

#### 역할 CRUD

- 역할 생성: 역할명, 코드, 설명 입력
- 역할 수정: 역할명, 설명 수정 (코드는 변경 불가)
- 역할 삭제: 사용자에게 배정된 역할은 삭제 불가, 시스템 역할은 삭제 불가
- 역할 목록 조회: 전체 역할 목록 및 각 역할에 배정된 사용자 수 표시

### 2.2 권한 관리

권한은 **리소스(resource)**와 **액션(action)**의 조합으로 정의한다.

#### 권한 체계

| 리소스 | 액션 | 권한 코드 | 설명 |
|--------|------|-----------|------|
| users | read | users:read | 사용자 조회 |
| users | write | users:write | 사용자 등록/수정 |
| users | delete | users:delete | 사용자 비활성화 |
| departments | read | departments:read | 부서 조회 |
| departments | write | departments:write | 부서 생성/수정 |
| departments | delete | departments:delete | 부서 비활성화 |
| roles | read | roles:read | 역할 조회 |
| roles | write | roles:write | 역할 생성/수정 |
| roles | admin | roles:admin | 역할 삭제, 권한 매핑 관리 |
| approvals | read | approvals:read | 결재 조회 |
| approvals | write | approvals:write | 결재 작성/제출 |
| approvals | admin | approvals:admin | 결재 관리 (양식, 결재선 설정) |
| boards | read | boards:read | 게시판 조회 |
| boards | write | boards:write | 게시글 작성/수정 |
| boards | admin | boards:admin | 게시판 관리 |
| system | admin | system:admin | 시스템 설정 관리 |

- 권한은 시스템에서 사전 정의하며, 관리자가 직접 생성하지 않는다.
- 새로운 모듈 추가 시 개발 단계에서 권한을 추가한다 (시드 데이터).

### 2.3 역할-권한 매핑

- 역할에 여러 권한을 매핑할 수 있다 (다대다 관계).
- 권한 매트릭스 뷰를 통해 역할별 권한을 한눈에 확인하고 수정할 수 있다.
- 기본 역할별 초기 권한 매핑:

**SYSTEM_ADMIN**: 모든 권한

**DEPT_ADMIN**:
- users:read, users:write
- departments:read
- roles:read
- approvals:read, approvals:write, approvals:admin
- boards:read, boards:write, boards:admin

**USER**:
- users:read (본인 정보만)
- departments:read
- approvals:read, approvals:write
- boards:read, boards:write

### 2.4 사용자-역할 매핑

- 사용자에게 하나 이상의 역할을 부여할 수 있다.
- 사용자의 최종 권한은 부여된 모든 역할의 권한을 합집합(Union)으로 계산한다.
- 사용자 등록 시 기본적으로 `USER` 역할을 부여한다.
- 역할 부여/해제는 시스템 관리자만 가능하다.

### 2.5 접근 제어

#### 백엔드 (FastAPI 미들웨어)

- API 요청 시 JWT 토큰에서 사용자 정보를 추출한다.
- 각 API 엔드포인트에 필요한 권한을 데코레이터 또는 의존성 주입으로 선언한다.
- 사용자의 역할로부터 권한을 조회하여 접근 허용/차단을 결정한다.
- 권한 부족 시 403 Forbidden을 반환한다.

```python
# 예시: FastAPI 의존성 주입
@router.get("/api/v1/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("users:read"))
):
    ...
```

#### 프론트엔드 (Next.js 라우트 가드)

- 로그인 시 사용자의 권한 목록을 가져온다 (`GET /api/v1/auth/me/permissions`).
- 권한 정보를 전역 상태(Context 또는 Zustand)에 저장한다.
- 라우트 가드: 페이지 접근 시 필요한 권한이 있는지 확인하고, 없으면 403 페이지로 리디렉션한다.
- 컴포넌트 가드: 버튼, 메뉴 항목 등을 권한에 따라 조건부 렌더링한다.

```tsx
// 예시: 권한 기반 조건부 렌더링
{hasPermission("users:write") && (
  <Button onClick={handleCreateUser}>사용자 등록</Button>
)}
```

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 권한 확인 로직은 요청당 10ms 이내에 완료 |
| 성능 | 사용자 권한 목록은 캐싱하여 매 요청마다 DB 조회를 방지 (Redis, TTL 5분) |
| 보안 | 백엔드에서의 권한 검증이 최종 권한 판단 기준 (프론트엔드 가드는 UX 목적) |
| 보안 | 권한 변경 시 해당 사용자의 캐시를 즉시 무효화 |
| 확장성 | 새로운 리소스/액션 추가 시 코드 변경 최소화 (데이터 기반 권한 관리) |
| 감사 | 역할 생성/수정/삭제, 권한 매핑 변경, 사용자 역할 변경을 감사 로그에 기록 |

## 4. 데이터베이스 스키마

### 4.1 `roles` 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 역할 고유 식별자 |
| name | VARCHAR(100) | NOT NULL | 역할명 (예: 시스템 관리자) |
| code | VARCHAR(50) | UNIQUE, NOT NULL | 역할 코드 (예: SYSTEM_ADMIN) |
| description | TEXT | NULL | 역할 설명 |
| is_system | BOOLEAN | NOT NULL, DEFAULT false | 시스템 내장 역할 여부 |
| created_by | UUID | FK → users.id, NULL | 생성자 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |
| updated_by | UUID | FK → users.id, NULL | 수정자 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 수정 시각 (UTC) |
| deleted_at | TIMESTAMPTZ | NULL | 소프트 삭제 시각 (UTC) |

**인덱스:**
- `idx_roles_code` — UNIQUE INDEX ON code WHERE deleted_at IS NULL
- `idx_roles_deleted_at` — INDEX ON deleted_at

### 4.2 `permissions` 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 권한 고유 식별자 |
| name | VARCHAR(100) | NOT NULL | 권한명 (예: 사용자 조회) |
| code | VARCHAR(100) | UNIQUE, NOT NULL | 권한 코드 (예: users:read) |
| resource | VARCHAR(50) | NOT NULL | 리소스 (예: users) |
| action | VARCHAR(50) | NOT NULL | 액션 (예: read, write, delete, admin) |
| description | TEXT | NULL | 권한 설명 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 수정 시각 (UTC) |

**인덱스:**
- `idx_permissions_code` — UNIQUE INDEX ON code
- `idx_permissions_resource` — INDEX ON resource
- `idx_permissions_resource_action` — UNIQUE INDEX ON (resource, action)

### 4.3 `role_permissions` 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| role_id | UUID | FK → roles.id, NOT NULL | 역할 참조 |
| permission_id | UUID | FK → permissions.id, NOT NULL | 권한 참조 |
| created_by | UUID | FK → users.id, NULL | 생성자 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |

**제약조건:**
- `pk_role_permissions` — PRIMARY KEY (role_id, permission_id)

**인덱스:**
- `idx_role_permissions_role_id` — INDEX ON role_id
- `idx_role_permissions_permission_id` — INDEX ON permission_id

### 4.4 `user_roles` 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| user_id | UUID | FK → users.id, NOT NULL | 사용자 참조 |
| role_id | UUID | FK → roles.id, NOT NULL | 역할 참조 |
| created_by | UUID | FK → users.id, NULL | 생성자 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |

**제약조건:**
- `pk_user_roles` — PRIMARY KEY (user_id, role_id)

**인덱스:**
- `idx_user_roles_user_id` — INDEX ON user_id
- `idx_user_roles_role_id` — INDEX ON role_id

## 5. API 명세

### 5.1 역할 API

#### GET /api/v1/roles

역할 목록을 조회한다.

**Headers:** `Authorization: Bearer {access_token}`

**필요 권한:** `roles:read`

**Response 200:**
```json
{
  "items": [
    {
      "id": "...",
      "name": "시스템 관리자",
      "code": "SYSTEM_ADMIN",
      "description": "모든 권한을 보유하며 시스템 전반을 관리합니다.",
      "is_system": true,
      "user_count": 2,
      "permission_count": 15,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "...",
      "name": "부서 관리자",
      "code": "DEPT_ADMIN",
      "description": "소속 부서 내 사용자 및 부서 설정을 관리합니다.",
      "is_system": true,
      "user_count": 10,
      "permission_count": 10,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "...",
      "name": "일반 사용자",
      "code": "USER",
      "description": "기본 그룹웨어 기능을 사용합니다.",
      "is_system": true,
      "user_count": 138,
      "permission_count": 6,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /api/v1/roles

역할을 생성한다. (시스템 관리자 전용)

**필요 권한:** `roles:write`

**Request Body:**
```json
{
  "name": "프로젝트 관리자",
  "code": "PROJECT_ADMIN",
  "description": "프로젝트 관련 리소스를 관리합니다."
}
```

**Response 201:**
```json
{
  "id": "...",
  "name": "프로젝트 관리자",
  "code": "PROJECT_ADMIN",
  "description": "프로젝트 관련 리소스를 관리합니다.",
  "is_system": false,
  "created_at": "2026-03-23T09:00:00Z"
}
```

**Response 409:**
```json
{
  "detail": "이미 존재하는 역할 코드입니다."
}
```

#### GET /api/v1/roles/{id}

역할 상세 정보를 조회한다 (매핑된 권한 목록 포함).

**필요 권한:** `roles:read`

**Response 200:**
```json
{
  "id": "...",
  "name": "부서 관리자",
  "code": "DEPT_ADMIN",
  "description": "소속 부서 내 사용자 및 부서 설정을 관리합니다.",
  "is_system": true,
  "permissions": [
    {
      "id": "...",
      "name": "사용자 조회",
      "code": "users:read",
      "resource": "users",
      "action": "read"
    },
    {
      "id": "...",
      "name": "사용자 등록/수정",
      "code": "users:write",
      "resource": "users",
      "action": "write"
    }
  ],
  "user_count": 10,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2026-03-20T14:00:00Z"
}
```

#### PUT /api/v1/roles/{id}

역할 정보를 수정한다. (시스템 관리자 전용)

**필요 권한:** `roles:write`

**Request Body:**
```json
{
  "name": "부서 관리자 (확장)",
  "description": "소속 부서 관리 및 결재 관리 권한을 포함합니다."
}
```

**Response 200:** — 수정된 역할 정보

**Response 400:**
```json
{
  "detail": "시스템 역할의 이름과 코드는 변경할 수 없습니다."
}
```

#### DELETE /api/v1/roles/{id}

역할을 삭제한다. (시스템 관리자 전용)

**필요 권한:** `roles:admin`

**Response 200:**
```json
{
  "message": "역할이 삭제되었습니다."
}
```

**Response 400:**
```json
{
  "detail": "시스템 역할은 삭제할 수 없습니다."
}
```

**Response 409:**
```json
{
  "detail": "해당 역할에 배정된 사용자가 존재합니다. 사용자의 역할을 먼저 변경해주세요."
}
```

### 5.2 권한 API

#### GET /api/v1/permissions

전체 권한 목록을 조회한다.

**필요 권한:** `roles:read`

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| resource | string | N | - | 특정 리소스의 권한만 조회 |

**Response 200:**
```json
{
  "items": [
    {
      "id": "...",
      "name": "사용자 조회",
      "code": "users:read",
      "resource": "users",
      "action": "read",
      "description": "사용자 목록 및 상세 정보를 조회할 수 있습니다."
    },
    {
      "id": "...",
      "name": "사용자 등록/수정",
      "code": "users:write",
      "resource": "users",
      "action": "write",
      "description": "사용자를 등록하고 정보를 수정할 수 있습니다."
    }
  ]
}
```

### 5.3 역할-권한 매핑 API

#### PUT /api/v1/roles/{id}/permissions

역할의 권한 매핑을 변경한다 (전체 교체 방식). (시스템 관리자 전용)

**필요 권한:** `roles:admin`

**Request Body:**
```json
{
  "permission_ids": [
    "permission-uuid-1",
    "permission-uuid-2",
    "permission-uuid-3"
  ]
}
```

**Response 200:**
```json
{
  "role_id": "...",
  "role_name": "부서 관리자",
  "permissions": [
    {
      "id": "permission-uuid-1",
      "code": "users:read",
      "name": "사용자 조회"
    },
    {
      "id": "permission-uuid-2",
      "code": "users:write",
      "name": "사용자 등록/수정"
    },
    {
      "id": "permission-uuid-3",
      "code": "departments:read",
      "name": "부서 조회"
    }
  ],
  "updated_at": "2026-03-23T10:00:00Z"
}
```

> 권한 매핑 변경 시 해당 역할을 가진 모든 사용자의 권한 캐시를 무효화한다.

### 5.4 사용자-역할 매핑 API

#### GET /api/v1/users/{id}/roles

사용자의 역할 목록을 조회한다.

**필요 권한:** `roles:read`

**Response 200:**
```json
{
  "user_id": "...",
  "roles": [
    {
      "id": "...",
      "name": "일반 사용자",
      "code": "USER",
      "is_system": true,
      "assigned_at": "2024-03-01T00:00:00Z"
    },
    {
      "id": "...",
      "name": "부서 관리자",
      "code": "DEPT_ADMIN",
      "is_system": true,
      "assigned_at": "2025-06-01T00:00:00Z"
    }
  ]
}
```

#### PUT /api/v1/users/{id}/roles

사용자의 역할을 변경한다 (전체 교체 방식). (시스템 관리자 전용)

**필요 권한:** `roles:admin`

**Request Body:**
```json
{
  "role_ids": [
    "role-uuid-user",
    "role-uuid-dept-admin"
  ]
}
```

**Response 200:**
```json
{
  "user_id": "...",
  "roles": [
    {
      "id": "role-uuid-user",
      "name": "일반 사용자",
      "code": "USER"
    },
    {
      "id": "role-uuid-dept-admin",
      "name": "부서 관리자",
      "code": "DEPT_ADMIN"
    }
  ],
  "updated_at": "2026-03-23T10:00:00Z"
}
```

> 역할 변경 시 해당 사용자의 권한 캐시를 즉시 무효화한다.

### 5.5 현재 사용자 권한 API

#### GET /api/v1/auth/me/permissions

현재 로그인한 사용자의 모든 권한을 조회한다.

**Headers:** `Authorization: Bearer {access_token}`

**Response 200:**
```json
{
  "user_id": "...",
  "roles": ["USER", "DEPT_ADMIN"],
  "permissions": [
    "users:read",
    "users:write",
    "departments:read",
    "roles:read",
    "approvals:read",
    "approvals:write",
    "approvals:admin",
    "boards:read",
    "boards:write",
    "boards:admin"
  ]
}
```

## 6. 화면 설계

### 6.1 역할 관리 페이지 (`/admin/roles`)

```
┌──────────────────────────────────────────────────────────────┐
│ 역할 관리                                      [+ 역할 추가] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 역할명          │ 코드          │ 유형   │ 사용자 │ 권한 │  │
│  ├─────────────────┼───────────────┼────────┼────────┼──────┤  │
│  │ 시스템 관리자    │ SYSTEM_ADMIN  │ 시스템 │   2명  │ 15개 │  │
│  │ 부서 관리자      │ DEPT_ADMIN    │ 시스템 │  10명  │ 10개 │  │
│  │ 일반 사용자      │ USER          │ 시스템 │ 138명  │  6개 │  │
│  │ 프로젝트 관리자  │ PROJECT_ADMIN │ 커스텀 │   5명  │  8개 │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  * 역할을 클릭하면 상세 정보 및 권한 매핑을 확인할 수 있습니다. │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 역할 목록 테이블: 역할명, 코드, 유형(시스템/커스텀), 배정 사용자 수, 권한 수
- 역할 클릭 시 상세 패널 또는 상세 페이지로 이동
- 시스템 역할은 삭제 버튼 비활성화, 유형 컬럼에 배지 표시
- 역할 추가 버튼: 모달로 역할 생성 폼 표시

### 6.2 역할 상세 페이지 (`/admin/roles/{id}`)

```
┌──────────────────────────────────────────────────────────────┐
│ ← 역할 목록                                                  │
│                                                              │
│ 부서 관리자 (DEPT_ADMIN)                     [수정] [삭제]   │
│ 소속 부서 내 사용자 및 부서 설정을 관리합니다.                 │
│ 유형: 시스템  |  사용자: 10명                                 │
├──────────────────────────────────────────────────────────────┤
│ [권한 설정]  [배정된 사용자]                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  권한 매핑                                       [저장]      │
│                                                              │
│  ┌──────────┬───────┬────────┬────────┬─────────┐           │
│  │ 리소스    │ read  │ write  │ delete │ admin   │           │
│  ├──────────┼───────┼────────┼────────┼─────────┤           │
│  │ users    │  [✓]  │  [✓]   │  [ ]   │  [ ]    │           │
│  │ departments│ [✓] │  [ ]   │  [ ]   │  [ ]    │           │
│  │ roles    │  [✓]  │  [ ]   │  [ ]   │  [ ]    │           │
│  │ approvals│  [✓]  │  [✓]   │  [ ]   │  [✓]    │           │
│  │ boards   │  [✓]  │  [✓]   │  [ ]   │  [✓]    │           │
│  │ system   │  [ ]  │  [ ]   │  [ ]   │  [ ]    │           │
│  └──────────┴───────┴────────┴────────┴─────────┘           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 상단: 역할 기본 정보 (이름, 코드, 설명, 유형, 배정 사용자 수)
- 탭: 권한 설정 / 배정된 사용자
- 권한 매트릭스: 리소스별 액션을 체크박스로 표시
  - 체크: 해당 권한이 매핑됨
  - 미체크: 해당 권한이 매핑되지 않음
  - 변경 후 저장 버튼으로 일괄 반영

### 6.3 배정된 사용자 탭

```
┌──────────────────────────────────────────────────────────────┐
│ [권한 설정]  [배정된 사용자]                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  배정된 사용자 (10명)                        [+ 사용자 추가]  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  이름     │ 사번          │ 부서     │ 배정일      │     │  │
│  ├───────────┼───────────────┼──────────┼─────────────┼─────┤  │
│  │ 홍길동    │ EMP-2024-001 │ 개발팀    │ 2025-06-01 │ [해제]│  │
│  │ 김철수    │ EMP-2024-002 │ 인사팀    │ 2025-07-15 │ [해제]│  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 해당 역할이 부여된 사용자 목록
- 사용자 추가 버튼: 사용자 검색 모달에서 사용자를 선택하여 역할 부여
- 해제 버튼: 해당 사용자에서 역할 제거 (확인 다이얼로그 표시)

### 6.4 사용자 상세 페이지 내 역할 탭

> 01-02 사용자 상세 페이지에 역할 탭을 추가한다.

```
┌──────────────────────────────────────────────────────────────┐
│ [기본 정보]  [소속 정보]  [역할/권한]  [활동 이력]              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  부여된 역할                                  [역할 변경]    │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐   │
│  │ [일반 사용자]  [부서 관리자]                             │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  보유 권한                                                   │
│                                                              │
│  users: 조회, 등록/수정                                       │
│  departments: 조회                                           │
│  roles: 조회                                                 │
│  approvals: 조회, 작성, 관리                                  │
│  boards: 조회, 작성, 관리                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 부여된 역할을 태그(칩) 형태로 표시
- 역할 변경 버튼: 역할 선택 모달 (체크박스로 다중 선택)
- 보유 권한: 리소스별로 그룹핑하여 표시 (읽기 전용)

## 7. 인수 조건

### 7.1 역할 관리

- [ ] 역할 목록을 조회할 수 있다 (역할명, 코드, 사용자 수, 권한 수 표시).
- [ ] 커스텀 역할을 생성할 수 있다.
- [ ] 역할 코드 중복 시 409 에러가 반환된다.
- [ ] 역할의 이름과 설명을 수정할 수 있다.
- [ ] 시스템 역할의 이름/코드 변경 시도 시 400 에러가 반환된다.
- [ ] 시스템 역할 삭제 시도 시 400 에러가 반환된다.
- [ ] 사용자가 배정된 역할 삭제 시도 시 409 에러가 반환된다.
- [ ] 사용자가 배정되지 않은 커스텀 역할은 삭제할 수 있다.

### 7.2 권한 관리

- [ ] 전체 권한 목록을 조회할 수 있다.
- [ ] 리소스별로 권한을 필터링하여 조회할 수 있다.

### 7.3 역할-권한 매핑

- [ ] 역할에 권한을 매핑할 수 있다 (권한 ID 목록으로 전체 교체).
- [ ] 매핑 변경 시 해당 역할의 모든 사용자 권한 캐시가 무효화된다.
- [ ] 권한 매트릭스 뷰에서 체크박스를 통해 권한을 설정할 수 있다.

### 7.4 사용자-역할 매핑

- [ ] 사용자에게 역할을 부여할 수 있다.
- [ ] 사용자에게 여러 역할을 동시에 부여할 수 있다.
- [ ] 사용자의 역할을 변경할 수 있다 (역할 ID 목록으로 전체 교체).
- [ ] 역할 변경 시 해당 사용자의 권한 캐시가 즉시 무효화된다.
- [ ] 사용자 등록 시 기본으로 USER 역할이 부여된다.

### 7.5 접근 제어 - 백엔드

- [ ] 권한이 없는 API 호출 시 403 Forbidden이 반환된다.
- [ ] SYSTEM_ADMIN 역할은 모든 API에 접근할 수 있다.
- [ ] 사용자의 최종 권한은 부여된 모든 역할 권한의 합집합이다.

### 7.6 접근 제어 - 프론트엔드

- [ ] 권한이 없는 페이지 접근 시 403 페이지가 표시된다.
- [ ] 권한이 없는 버튼/메뉴는 화면에 표시되지 않는다.
- [ ] 로그인 시 권한 목록을 가져와 전역 상태에 저장한다.

## 8. 참고사항

- 권한 확인 흐름: JWT에서 user_id 추출 → Redis 캐시에서 권한 목록 조회 → 캐시 미스 시 DB에서 user_roles + role_permissions를 조인하여 조회 후 캐시 저장
- SYSTEM_ADMIN 역할은 코드 레벨에서 모든 권한을 우회하는 로직을 별도로 구현한다 (DB에 모든 권한을 매핑하는 것이 아닌, 미들웨어에서 SYSTEM_ADMIN이면 항상 통과).
- 권한 시드 데이터: 마이그레이션 스크립트에서 기본 역할과 권한을 생성한다. 새로운 모듈 추가 시 마이그레이션으로 권한을 추가한다.
- 부서 관리자(DEPT_ADMIN)의 범위 제한: 부서 관리자는 자신의 소속 부서(및 하위 부서) 내 사용자만 관리할 수 있다. 이 범위 제한은 권한 체크와 별도로 비즈니스 로직에서 처리한다.
- 향후 확장 고려사항:
  - 속성 기반 접근 제어(ABAC) 도입 시 현재 RBAC 위에 레이어를 추가하는 방식으로 확장
  - 부서별 역할(부서 내에서만 유효한 역할) 도입 검토
  - API rate limiting을 역할별로 차등 적용 검토
- 프론트엔드에서 `usePermission` 커스텀 훅을 제공하여 컴포넌트에서 쉽게 권한을 확인할 수 있도록 한다.

```tsx
// 사용 예시
const { hasPermission, hasAnyPermission, hasAllPermissions } = usePermission();

if (hasPermission("users:write")) {
  // 사용자 등록 버튼 렌더링
}
```
