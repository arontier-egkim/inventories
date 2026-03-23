# 01-01 인증 시스템 (Authentication)

## 1. 개요

그룹웨어 시스템의 인증 기반을 구축한다. 이메일과 비밀번호를 이용한 로그인/로그아웃 기능을 제공하며, JWT 기반의 토큰 인증 방식을 사용한다. 비밀번호 재설정, 초기 비밀번호 변경 강제, 동시 로그인 제한 등 엔터프라이즈 수준의 인증 정책을 적용한다.

- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)
- **의존성**: 없음 (최초 모듈)

## 2. 기능 요구사항

### 2.1 로그인

- 이메일 + 비밀번호 조합으로 로그인한다.
- 로그인 성공 시 JWT access token과 refresh token을 발급한다.
  - Access token 유효기간: **30분**
  - Refresh token 유효기간: **7일**
- Access token은 응답 body로 전달하고, refresh token은 `HttpOnly` 쿠키로 설정한다.
- 로그인 실패 시 실패 횟수를 기록하며, **5회 연속 실패 시 계정을 10분간 잠금**한다.
- 비활성화(`is_active = false`) 상태의 계정은 로그인을 차단한다.
- 로그인 성공 시 `last_login_at`을 갱신한다.

### 2.2 로그아웃

- 현재 세션의 refresh token을 무효화(`revoked_at` 기록)한다.
- 클라이언트 측 access token을 삭제한다.
- HttpOnly 쿠키의 refresh token을 제거한다.

### 2.3 토큰 갱신

- 유효한 refresh token을 이용하여 새로운 access token을 발급한다.
- Refresh token rotation: 갱신 시 기존 refresh token을 폐기하고 새 refresh token을 발급한다.
- 폐기된 refresh token으로 갱신 시도 시 해당 사용자의 **모든 refresh token을 무효화**한다 (탈취 감지).

### 2.4 비밀번호 재설정

- 이메일 주소를 입력하면 비밀번호 재설정 링크를 발송한다.
- 재설정 토큰 유효기간: **1시간**
- 재설정 토큰은 1회 사용 후 무효화한다.
- 새 비밀번호는 비밀번호 정책을 준수해야 한다.
- 비밀번호 변경 성공 시 해당 사용자의 모든 refresh token을 무효화한다.

### 2.5 초기 비밀번호 변경 강제

- `must_change_password = true`인 사용자는 로그인 후 비밀번호 변경 화면으로 강제 리디렉션한다.
- 비밀번호 변경 완료 전까지 다른 API 호출을 차단한다 (비밀번호 변경 API 제외).
- 관리자가 사용자를 등록하거나 비밀번호를 초기화할 때 `must_change_password = true`로 설정한다.

### 2.6 동시 로그인 정책

- 사용자당 최대 **3개의 활성 세션**을 허용한다.
- 4번째 로그인 시 가장 오래된 세션의 refresh token을 자동으로 무효화한다.
- 관리자는 특정 사용자의 모든 세션을 강제 종료할 수 있다.

### 2.7 비밀번호 정책

- 최소 **8자 이상**
- **영문 대소문자, 숫자, 특수문자** 중 3종류 이상 포함
- 이전 비밀번호 **3개와 동일한 비밀번호** 사용 불가
- 비밀번호 해싱: **bcrypt** (cost factor 12)

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 보안 | 비밀번호는 bcrypt로 해싱하여 저장, 평문 저장 절대 불가 |
| 보안 | JWT 서명에 RS256 알고리즘 사용 |
| 보안 | Refresh token은 HttpOnly, Secure, SameSite=Strict 쿠키로 관리 |
| 보안 | 로그인 API에 rate limiting 적용 (IP당 분당 10회) |
| 성능 | 로그인 API 응답 시간 500ms 이내 |
| 가용성 | 인증 서비스 가용률 99.9% 이상 |
| 감사 | 로그인 성공/실패, 비밀번호 변경, 토큰 갱신 등 모든 인증 이벤트를 로그로 기록 |

## 4. 데이터베이스 스키마

### 4.1 `users` 테이블

> 이 태스크에서는 인증 관련 컬럼만 정의한다. 프로필 관련 컬럼은 01-02에서 확장한다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 사용자 고유 식별자 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 로그인 이메일 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 해싱된 비밀번호 |
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
- `idx_users_deleted_at` — INDEX ON deleted_at

### 4.2 `refresh_tokens` 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 토큰 고유 식별자 |
| user_id | UUID | FK → users.id, NOT NULL | 사용자 참조 |
| token | VARCHAR(512) | UNIQUE, NOT NULL | Refresh token 값 |
| user_agent | VARCHAR(512) | NULL | 접속 기기 정보 |
| ip_address | VARCHAR(45) | NULL | 접속 IP 주소 |
| expires_at | TIMESTAMPTZ | NOT NULL | 만료 시각 (UTC) |
| revoked_at | TIMESTAMPTZ | NULL | 폐기 시각 (UTC), NULL이면 유효 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |

**인덱스:**
- `idx_refresh_tokens_user_id` — INDEX ON user_id
- `idx_refresh_tokens_token` — UNIQUE INDEX ON token
- `idx_refresh_tokens_expires_at` — INDEX ON expires_at

### 4.3 `password_histories` 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 고유 식별자 |
| user_id | UUID | FK → users.id, NOT NULL | 사용자 참조 |
| password_hash | VARCHAR(255) | NOT NULL | 이전 비밀번호 해시 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |

**인덱스:**
- `idx_password_histories_user_id` — INDEX ON user_id

### 4.4 `password_reset_tokens` 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 고유 식별자 |
| user_id | UUID | FK → users.id, NOT NULL | 사용자 참조 |
| token | VARCHAR(512) | UNIQUE, NOT NULL | 재설정 토큰 |
| expires_at | TIMESTAMPTZ | NOT NULL | 만료 시각 (UTC) |
| used_at | TIMESTAMPTZ | NULL | 사용 시각 (UTC), NULL이면 미사용 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 (UTC) |

**인덱스:**
- `idx_password_reset_tokens_token` — UNIQUE INDEX ON token
- `idx_password_reset_tokens_user_id` — INDEX ON user_id

## 5. API 명세

### 5.1 POST /api/v1/auth/login

로그인을 수행하고 토큰을 발급한다.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "P@ssw0rd!"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "must_change_password": false
  }
}
```
> Refresh token은 `Set-Cookie` 헤더로 전달 (`HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/api/v1/auth`)

**Response 401:**
```json
{
  "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

**Response 423:**
```json
{
  "detail": "계정이 잠겨 있습니다. 10분 후 다시 시도해주세요.",
  "locked_until": "2026-03-23T10:30:00Z"
}
```

### 5.2 POST /api/v1/auth/logout

현재 세션을 종료하고 refresh token을 무효화한다.

**Headers:** `Authorization: Bearer {access_token}`

**Response 200:**
```json
{
  "message": "로그아웃되었습니다."
}
```

### 5.3 POST /api/v1/auth/refresh

Access token을 갱신한다.

**Request:** 쿠키에 포함된 refresh token 사용 (body 없음)

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 1800
}
```

**Response 401:**
```json
{
  "detail": "유효하지 않거나 만료된 리프레시 토큰입니다."
}
```

### 5.4 POST /api/v1/auth/password-reset/request

비밀번호 재설정 이메일을 발송한다.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response 200:**
```json
{
  "message": "비밀번호 재설정 이메일이 발송되었습니다."
}
```
> 보안상 존재하지 않는 이메일이라도 동일한 성공 응답을 반환한다.

### 5.5 POST /api/v1/auth/password-reset/confirm

비밀번호를 재설정한다.

**Request Body:**
```json
{
  "token": "reset-token-value",
  "new_password": "N3wP@ssw0rd!"
}
```

**Response 200:**
```json
{
  "message": "비밀번호가 성공적으로 변경되었습니다."
}
```

**Response 400:**
```json
{
  "detail": "유효하지 않거나 만료된 재설정 토큰입니다."
}
```

**Response 422:**
```json
{
  "detail": "비밀번호 정책을 충족하지 않습니다.",
  "errors": [
    "비밀번호는 8자 이상이어야 합니다.",
    "영문, 숫자, 특수문자 중 3종류 이상 포함해야 합니다."
  ]
}
```

### 5.6 PUT /api/v1/auth/password

비밀번호를 변경한다 (로그인 상태에서).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "current_password": "OldP@ssw0rd!",
  "new_password": "N3wP@ssw0rd!"
}
```

**Response 200:**
```json
{
  "message": "비밀번호가 성공적으로 변경되었습니다."
}
```

**Response 400:**
```json
{
  "detail": "현재 비밀번호가 올바르지 않습니다."
}
```

**Response 422:**
```json
{
  "detail": "이전에 사용한 비밀번호는 사용할 수 없습니다."
}
```

## 6. 화면 설계

### 6.1 로그인 페이지 (`/login`)

```
┌─────────────────────────────────────────┐
│                                         │
│            [회사 로고]                    │
│           그룹웨어 시스템                  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 이메일                           │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ 비밀번호                         │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [        로그인        ]               │
│                                         │
│  비밀번호를 잊으셨나요?                    │
│                                         │
└─────────────────────────────────────────┘
```

- 이메일 입력 필드: 이메일 형식 유효성 검사
- 비밀번호 입력 필드: 마스킹 처리, 눈 아이콘으로 표시/숨기기 토글
- 로그인 버튼: 입력값 검증 후 로그인 API 호출
- "비밀번호를 잊으셨나요?" 링크: 비밀번호 재설정 페이지로 이동
- 로그인 실패 시 에러 메시지를 입력 폼 상단에 표시
- 계정 잠금 시 잠금 해제까지 남은 시간을 표시

### 6.2 비밀번호 재설정 요청 페이지 (`/password-reset`)

```
┌─────────────────────────────────────────┐
│                                         │
│           비밀번호 재설정                  │
│                                         │
│  가입된 이메일을 입력하시면               │
│  비밀번호 재설정 링크를 보내드립니다.      │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 이메일                           │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [     재설정 링크 발송     ]            │
│                                         │
│  ← 로그인으로 돌아가기                    │
│                                         │
└─────────────────────────────────────────┘
```

### 6.3 비밀번호 재설정 확인 페이지 (`/password-reset/confirm?token=...`)

```
┌─────────────────────────────────────────┐
│                                         │
│          새 비밀번호 설정                  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 새 비밀번호                       │    │
│  └─────────────────────────────────┘    │
│  ○ 8자 이상  ○ 영문 포함              │
│  ○ 숫자 포함  ○ 특수문자 포함          │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 새 비밀번호 확인                   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [     비밀번호 변경     ]               │
│                                         │
└─────────────────────────────────────────┘
```

- 비밀번호 정책 충족 여부를 실시간으로 체크 표시 (충족 시 녹색 체크, 미충족 시 회색 원)
- 비밀번호 확인 필드 일치 여부 실시간 표시

### 6.4 초기 비밀번호 변경 페이지 (`/change-password`)

```
┌─────────────────────────────────────────┐
│                                         │
│       초기 비밀번호를 변경해주세요         │
│                                         │
│  보안을 위해 비밀번호를 변경해야           │
│  서비스를 이용할 수 있습니다.             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 현재 비밀번호                     │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ 새 비밀번호                       │    │
│  └─────────────────────────────────┘    │
│  ○ 8자 이상  ○ 영문 포함              │
│  ○ 숫자 포함  ○ 특수문자 포함          │
│  ┌─────────────────────────────────┐    │
│  │ 새 비밀번호 확인                   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [     비밀번호 변경     ]               │
│                                         │
└─────────────────────────────────────────┘
```

- `must_change_password = true`인 경우 로그인 직후 이 페이지로 리디렉션
- 다른 페이지 접근 시도 시 이 페이지로 재리디렉션

## 7. 인수 조건

### 7.1 로그인

- [ ] 올바른 이메일/비밀번호로 로그인 시 access token과 refresh token이 발급된다.
- [ ] 잘못된 이메일 또는 비밀번호로 로그인 시 401 에러가 반환된다.
- [ ] 5회 연속 로그인 실패 시 계정이 10분간 잠긴다.
- [ ] 비활성화된 계정으로 로그인 시도 시 로그인이 차단된다.
- [ ] 로그인 성공 시 `last_login_at`이 갱신된다.

### 7.2 로그아웃

- [ ] 로그아웃 시 해당 refresh token이 무효화된다.
- [ ] 로그아웃 후 이전 refresh token으로 갱신 시도 시 실패한다.

### 7.3 토큰 갱신

- [ ] 유효한 refresh token으로 새 access token을 발급받을 수 있다.
- [ ] 만료된 refresh token으로 갱신 시도 시 401 에러가 반환된다.
- [ ] 폐기된 refresh token으로 갱신 시도 시 해당 사용자의 모든 토큰이 무효화된다.

### 7.4 비밀번호 재설정

- [ ] 유효한 이메일 입력 시 재설정 이메일이 발송된다.
- [ ] 존재하지 않는 이메일 입력 시에도 성공 응답이 반환된다.
- [ ] 재설정 토큰으로 비밀번호를 변경할 수 있다.
- [ ] 1시간 경과 후 토큰은 만료된다.
- [ ] 사용된 토큰으로 재시도 시 실패한다.

### 7.5 비밀번호 정책

- [ ] 8자 미만 비밀번호는 거부된다.
- [ ] 영문+숫자+특수문자 중 3종류 미만 포함 시 거부된다.
- [ ] 최근 3개 비밀번호와 동일한 비밀번호는 거부된다.

### 7.6 동시 로그인

- [ ] 3개 세션까지는 동시 로그인이 가능하다.
- [ ] 4번째 로그인 시 가장 오래된 세션이 자동 종료된다.

### 7.7 초기 비밀번호 변경

- [ ] `must_change_password = true`인 사용자는 로그인 후 비밀번호 변경 화면으로 리디렉션된다.
- [ ] 비밀번호 변경 완료 후 `must_change_password`가 false로 변경된다.

## 8. 참고사항

- JWT 페이로드에는 `user_id`, `email`, `roles` 정보를 포함한다.
- Access token은 프론트엔드에서 메모리(변수)에 저장하고, localStorage/sessionStorage에 저장하지 않는다.
- 프론트엔드에서 access token 만료 시 자동으로 refresh API를 호출하는 인터셉터를 구현한다 (Axios 인터셉터 또는 fetch wrapper).
- 비밀번호 재설정 이메일 발송은 비동기 큐(Celery 등)로 처리하여 API 응답 지연을 방지한다.
- 모든 인증 관련 이벤트(로그인 성공/실패, 로그아웃, 비밀번호 변경 등)는 감사 로그 테이블에 기록한다.
- CORS 설정에서 허용 도메인을 엄격히 관리한다.
