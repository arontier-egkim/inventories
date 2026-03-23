# 03-01 공지사항 게시판

## 1. 개요

전사 공지사항을 등록, 조회, 관리하는 모듈이다. 관리자 또는 부서관리자만 공지사항을 작성할 수 있으며, 일반 사용자는 조회만 가능하다. 공지 상단 고정, 팝업 공지, 필독 확인 등 그룹웨어에서 필수적인 기능을 제공한다.

- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)
- **의존성**: `01-04` 권한 관리 (작성 권한 제어)
- **관련 모듈**: `03-03` 첨부파일 및 댓글 (공통 모듈)

## 2. 기능 요구사항

### 2.1 공지사항 CRUD

| 구분 | 설명 |
|------|------|
| 작성 | 관리자 또는 부서관리자가 공지사항을 작성한다. 제목, 내용(Rich Text), 카테고리, 옵션(상단 고정, 팝업, 필독)을 설정할 수 있다. |
| 조회 | 모든 로그인 사용자가 공지사항 목록 및 상세를 조회할 수 있다. |
| 수정 | 작성자 본인 또는 관리자가 공지사항을 수정할 수 있다. |
| 삭제 | 작성자 본인 또는 관리자가 공지사항을 삭제(소프트 삭제)할 수 있다. |

### 2.2 카테고리 관리

- 기본 카테고리: **인사**, **총무**, **IT**, **경영**, **기타**
- 관리자가 카테고리를 추가/수정/삭제할 수 있다.
- 카테고리별 정렬 순서(sort_order)를 지정할 수 있다.

### 2.3 공지 상단 고정

- `is_pinned` 플래그로 상단 고정 여부를 설정한다.
- `pin_expires_at`으로 고정 만료 일시를 지정할 수 있다 (선택 사항).
- 만료 일시가 지나면 자동으로 고정이 해제된다.
- 고정된 공지는 목록 최상단에 별도 영역으로 표시된다.

### 2.4 팝업 공지

- `is_popup` 플래그로 팝업 공지 여부를 설정한다.
- `popup_start_date` ~ `popup_end_date` 기간 동안 로그인 시 모달로 표시된다.
- 사용자가 "오늘 하루 보지 않기"를 선택하면 해당 일자에는 다시 표시하지 않는다.
- 팝업 기간이 종료되면 자동으로 일반 공지로 전환된다.

### 2.5 필독 확인

- `is_must_read` 플래그로 필독 공지 여부를 설정한다.
- 필독 공지는 목록에서 별도 배지로 표시된다.
- 사용자가 상세 페이지에서 "읽음 확인" 버튼을 클릭하면 읽음 기록이 생성된다.
- 관리자는 필독 공지에 대한 읽음 현황(읽은 사람/안 읽은 사람)을 확인할 수 있다.

### 2.6 조회수 카운트

- 사용자가 공지사항 상세를 조회할 때마다 조회수가 1 증가한다.
- 동일 사용자의 연속 조회는 중복 카운트하지 않는다 (세션 기준 또는 일정 시간 간격).

### 2.7 목록 조회

- 페이지네이션 (기본 20건)
- 카테고리 필터
- 검색: 제목, 내용, 제목+내용
- 정렬: 최신순 (기본), 조회수순
- 상단 고정 공지는 항상 최상단에 표시

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 목록 조회 API 응답 시간 500ms 이내 |
| 보안 | 작성/수정/삭제는 권한 검증 필수 (01-04 권한 모듈 연동) |
| 데이터 보존 | 소프트 삭제 적용 (deleted_at), 물리 삭제 없음 |
| 동시성 | 조회수 업데이트 시 race condition 방지 (DB 레벨 원자적 증가) |
| 캐싱 | 팝업 공지 목록은 Redis 캐시 적용 (TTL 5분) |

## 4. 데이터베이스 스키마

### 4.1 notice_categories (공지 카테고리)

```sql
CREATE TABLE notice_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,          -- 카테고리명 (예: '인사')
    code VARCHAR(20) NOT NULL UNIQUE,   -- 카테고리 코드 (예: 'HR')
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

-- 초기 데이터
INSERT INTO notice_categories (name, code, sort_order, created_by) VALUES
('인사', 'HR', 1, '<admin_uuid>'),
('총무', 'GA', 2, '<admin_uuid>'),
('IT', 'IT', 3, '<admin_uuid>'),
('경영', 'MGMT', 4, '<admin_uuid>'),
('기타', 'ETC', 5, '<admin_uuid>');
```

### 4.2 notices (공지사항)

```sql
CREATE TABLE notices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,                       -- Rich Text (HTML)
    category_id UUID NOT NULL REFERENCES notice_categories(id),
    author_id UUID NOT NULL REFERENCES users(id),
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    pin_expires_at TIMESTAMPTZ,                  -- 고정 만료 일시 (NULL이면 무기한)
    is_popup BOOLEAN NOT NULL DEFAULT FALSE,
    popup_start_date DATE,                       -- 팝업 시작일
    popup_end_date DATE,                         -- 팝업 종료일
    is_must_read BOOLEAN NOT NULL DEFAULT FALSE,
    view_count INTEGER NOT NULL DEFAULT 0,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_notices_category_id ON notices(category_id);
CREATE INDEX idx_notices_author_id ON notices(author_id);
CREATE INDEX idx_notices_is_pinned ON notices(is_pinned) WHERE deleted_at IS NULL;
CREATE INDEX idx_notices_is_popup ON notices(is_popup) WHERE deleted_at IS NULL;
CREATE INDEX idx_notices_created_at ON notices(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_notices_search ON notices USING gin(to_tsvector('korean', title || ' ' || content)) WHERE deleted_at IS NULL;
```

### 4.3 notice_reads (읽음 기록)

```sql
CREATE TABLE notice_reads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notice_id UUID NOT NULL REFERENCES notices(id),
    user_id UUID NOT NULL REFERENCES users(id),
    read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(notice_id, user_id)
);

CREATE INDEX idx_notice_reads_notice_id ON notice_reads(notice_id);
CREATE INDEX idx_notice_reads_user_id ON notice_reads(user_id);
```

### ERD 요약

```
notice_categories 1──N notices
users             1──N notices (author_id)
notices           1──N notice_reads
users             1──N notice_reads (user_id)
notices           1──N attachments (attachable_type='NOTICE', 03-03 참조)
notices           1──N comments (commentable_type='NOTICE', 03-03 참조)
```

## 5. API 명세

### 5.1 공지사항 목록 조회

```
GET /api/v1/notices
```

**쿼리 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | integer | N | 페이지 번호 (기본: 1) |
| size | integer | N | 페이지 크기 (기본: 20, 최대: 100) |
| category | string | N | 카테고리 코드 (예: HR, IT) |
| search | string | N | 검색어 |
| search_type | string | N | 검색 유형: title, content, all (기본: all) |
| sort | string | N | 정렬: latest (기본), views |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "pinned": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "title": "[필독] 2026년 연간 업무 계획 안내",
        "category": {
          "id": "...",
          "name": "경영",
          "code": "MGMT"
        },
        "author": {
          "id": "...",
          "name": "김관리",
          "department": "경영지원팀"
        },
        "is_pinned": true,
        "is_must_read": true,
        "view_count": 342,
        "created_at": "2026-03-20T09:00:00Z"
      }
    ],
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "title": "3월 사내 교육 일정 안내",
        "category": {
          "id": "...",
          "name": "인사",
          "code": "HR"
        },
        "author": {
          "id": "...",
          "name": "이인사",
          "department": "인사팀"
        },
        "is_pinned": false,
        "is_must_read": false,
        "view_count": 128,
        "has_attachment": true,
        "created_at": "2026-03-22T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total_count": 156,
      "total_pages": 8
    }
  }
}
```

### 5.2 공지사항 상세 조회

```
GET /api/v1/notices/{id}
```

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "3월 사내 교육 일정 안내",
    "content": "<p>안녕하세요. 인사팀입니다.</p><p>3월 사내 교육 일정을 안내드립니다...</p>",
    "category": {
      "id": "...",
      "name": "인사",
      "code": "HR"
    },
    "author": {
      "id": "...",
      "name": "이인사",
      "department": "인사팀"
    },
    "is_pinned": false,
    "pin_expires_at": null,
    "is_popup": false,
    "popup_start_date": null,
    "popup_end_date": null,
    "is_must_read": false,
    "view_count": 129,
    "is_read": true,
    "attachments": [
      {
        "id": "...",
        "file_name": "3월_교육일정.pdf",
        "file_size": 1048576,
        "mime_type": "application/pdf"
      }
    ],
    "created_at": "2026-03-22T14:30:00Z",
    "updated_at": null
  }
}
```

### 5.3 공지사항 작성

```
POST /api/v1/notices
```

**권한**: 관리자 또는 부서관리자

**요청 본문**

```json
{
  "title": "4월 휴무일 안내",
  "content": "<p>4월 휴무일을 안내드립니다...</p>",
  "category_id": "550e8400-e29b-41d4-a716-446655440010",
  "is_pinned": true,
  "pin_expires_at": "2026-04-01T00:00:00Z",
  "is_popup": true,
  "popup_start_date": "2026-03-25",
  "popup_end_date": "2026-03-31",
  "is_must_read": false,
  "attachment_ids": ["...", "..."]
}
```

**응답 (201 Created)**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440099",
    "title": "4월 휴무일 안내",
    "created_at": "2026-03-23T10:00:00Z"
  }
}
```

### 5.4 공지사항 수정

```
PUT /api/v1/notices/{id}
```

**권한**: 작성자 본인 또는 관리자

**요청 본문**

```json
{
  "title": "4월 휴무일 안내 (수정)",
  "content": "<p>수정된 내용입니다...</p>",
  "category_id": "550e8400-e29b-41d4-a716-446655440010",
  "is_pinned": true,
  "pin_expires_at": "2026-04-05T00:00:00Z",
  "is_popup": false,
  "is_must_read": false
}
```

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440099",
    "title": "4월 휴무일 안내 (수정)",
    "updated_at": "2026-03-23T11:00:00Z"
  }
}
```

### 5.5 공지사항 삭제

```
DELETE /api/v1/notices/{id}
```

**권한**: 작성자 본인 또는 관리자

**응답 (200 OK)**

```json
{
  "success": true,
  "message": "공지사항이 삭제되었습니다."
}
```

### 5.6 읽음 확인

```
POST /api/v1/notices/{id}/read
```

**설명**: 현재 로그인 사용자의 읽음 기록을 생성한다. 이미 읽음 처리된 경우 중복 생성하지 않는다.

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "notice_id": "550e8400-e29b-41d4-a716-446655440001",
    "read_at": "2026-03-23T09:30:00Z"
  }
}
```

### 5.7 읽음 현황 조회

```
GET /api/v1/notices/{id}/readers
```

**권한**: 관리자 또는 해당 공지 작성자

**쿼리 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| status | string | N | read (읽음), unread (미읽음), all (기본) |
| page | integer | N | 페이지 번호 (기본: 1) |
| size | integer | N | 페이지 크기 (기본: 50) |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "summary": {
      "total_users": 150,
      "read_count": 98,
      "unread_count": 52,
      "read_rate": 65.3
    },
    "items": [
      {
        "user_id": "...",
        "name": "박사원",
        "department": "개발팀",
        "is_read": true,
        "read_at": "2026-03-21T10:15:00Z"
      },
      {
        "user_id": "...",
        "name": "최사원",
        "department": "디자인팀",
        "is_read": false,
        "read_at": null
      }
    ],
    "pagination": {
      "page": 1,
      "size": 50,
      "total_count": 150,
      "total_pages": 3
    }
  }
}
```

### 5.8 팝업 공지 조회

```
GET /api/v1/notices/popup
```

**설명**: 현재 활성화된 팝업 공지 목록을 반환한다. 오늘 날짜가 `popup_start_date` ~ `popup_end_date` 범위에 포함되고, 사용자가 "오늘 하루 보지 않기"를 선택하지 않은 공지만 반환한다.

**응답 (200 OK)**

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440050",
      "title": "시스템 점검 안내",
      "content": "<p>3월 25일 새벽 2시~5시 시스템 점검이 예정되어 있습니다.</p>",
      "popup_start_date": "2026-03-22",
      "popup_end_date": "2026-03-25"
    }
  ]
}
```

### 5.9 에러 응답 공통 형식

```json
{
  "success": false,
  "error": {
    "code": "NOTICE_NOT_FOUND",
    "message": "해당 공지사항을 찾을 수 없습니다."
  }
}
```

| 에러 코드 | HTTP 상태 | 설명 |
|-----------|-----------|------|
| NOTICE_NOT_FOUND | 404 | 공지사항이 존재하지 않거나 삭제됨 |
| NOTICE_FORBIDDEN | 403 | 작성/수정/삭제 권한 없음 |
| NOTICE_INVALID_CATEGORY | 400 | 유효하지 않은 카테고리 |
| NOTICE_INVALID_POPUP_DATE | 400 | 팝업 시작일이 종료일보다 늦음 |

## 6. 화면 설계

### 6.1 공지사항 목록 화면

```
+------------------------------------------------------------------+
| 공지사항                                            [공지 작성]   |
+------------------------------------------------------------------+
| 카테고리: [전체 v]  검색: [제목+내용 v] [검색어 입력...] [검색]   |
+------------------------------------------------------------------+
| □ | 구분   | 제목                        | 작성자 | 날짜   | 조회 |
+---+--------+-----------------------------+--------+--------+------+
|   | 📌필독 | [경영] 2026년 연간 업무 계획 | 김관리 | 03-20 | 342  |
|   | 📌     | [IT] 시스템 점검 안내        | 박전산 | 03-19 | 256  |
+---+--------+-----------------------------+--------+--------+------+
|   |        | [인사] 3월 사내 교육 일정    | 이인사 | 03-22 | 128  |
|   |        | [총무] 사무용품 신청 안내    | 정총무 | 03-21 |  95  |
|   |        | [기타] 동호회 모집 안내      | 최사원 | 03-20 |  67  |
+---+--------+-----------------------------+--------+--------+------+
|                    < 1  2  3  4  5 ... 8 >                       |
+------------------------------------------------------------------+
```

- 상단 고정 공지는 배경색을 구분하여 표시한다.
- 필독 공지에는 "필독" 배지를 표시한다.
- 첨부파일이 있는 게시글에는 클립 아이콘을 표시한다.
- 카테고리는 대괄호로 제목 앞에 표시한다.

### 6.2 공지사항 상세 화면

```
+------------------------------------------------------------------+
| < 목록으로                                                        |
+------------------------------------------------------------------+
| [인사] 3월 사내 교육 일정 안내                                     |
| 작성자: 이인사 (인사팀) | 작성일: 2026-03-22 14:30 | 조회: 129   |
+------------------------------------------------------------------+
|                                                                    |
| 안녕하세요. 인사팀입니다.                                          |
| 3월 사내 교육 일정을 안내드립니다.                                  |
|                                                                    |
| 1. 직무교육 - 3월 25일 (화) 14:00~16:00                           |
| 2. 안전교육 - 3월 27일 (목) 10:00~12:00                           |
|                                                                    |
+------------------------------------------------------------------+
| 첨부파일                                                          |
| 📎 3월_교육일정.pdf (1.0MB) [다운로드]                            |
| 📎 교육장_안내도.png (256KB) [다운로드]                           |
+------------------------------------------------------------------+
| [읽음 확인]  ※ 필독 공지인 경우에만 표시                          |
| 읽음 현황: 98/150명 (65.3%)  [상세 보기]  ※ 관리자에게만 표시     |
+------------------------------------------------------------------+
| 댓글 (3)                                                          |
| ┌─ 박사원 (개발팀) | 03-22 15:00                                  |
| │  교육 장소가 어디인가요?                                         |
| │  └─ 이인사 (인사팀) | 03-22 15:30                               |
| │     본관 3층 대회의실입니다.                                      |
| ├─ 최사원 (디자인팀) | 03-22 16:00                                |
| │  확인했습니다. 감사합니다.                                       |
+------------------------------------------------------------------+
| 댓글 작성                                                         |
| [댓글 내용 입력...]                                    [등록]     |
+------------------------------------------------------------------+
|                           [수정] [삭제]  ※ 작성자/관리자만 표시   |
+------------------------------------------------------------------+
```

### 6.3 공지사항 작성/수정 폼

```
+------------------------------------------------------------------+
| 공지사항 작성                                                      |
+------------------------------------------------------------------+
| 카테고리 *  [인사 v]                                              |
| 제목 *      [제목을 입력하세요...]                                 |
+------------------------------------------------------------------+
| [Rich Text Editor - 서식 도구 모음]                                |
| [B] [I] [U] [H1] [H2] [목록] [링크] [이미지] [표]               |
|                                                                    |
| [본문 내용을 입력하세요...]                                        |
|                                                                    |
+------------------------------------------------------------------+
| 첨부파일                                                          |
| [파일을 드래그하여 놓거나 클릭하여 업로드] (최대 50MB/파일)        |
| 📎 업로드된파일.pdf (1.0MB) [X]                                   |
+------------------------------------------------------------------+
| 옵션                                                              |
| ☑ 상단 고정   만료일: [2026-04-01]                                |
| ☐ 팝업 공지   시작일: [____-__-__]  종료일: [____-__-__]         |
| ☐ 필독 공지                                                      |
+------------------------------------------------------------------+
|                                          [취소]  [임시저장]  [등록] |
+------------------------------------------------------------------+
```

### 6.4 팝업 공지 모달

```
+----------------------------------------------+
| ⓘ 공지사항                            [X]   |
+----------------------------------------------+
|                                              |
| 시스템 점검 안내                              |
|                                              |
| 3월 25일 새벽 2시~5시                         |
| 시스템 점검이 예정되어 있습니다.               |
| 해당 시간에는 서비스 이용이 제한됩니다.        |
|                                              |
|              [자세히 보기]                    |
+----------------------------------------------+
| ☐ 오늘 하루 보지 않기               [닫기]   |
+----------------------------------------------+
```

- 활성화된 팝업 공지가 여러 건인 경우 슬라이드 또는 순차 표시한다.
- "자세히 보기"를 클릭하면 공지 상세 페이지로 이동한다.

## 7. 인수 조건

### 7.1 공지사항 CRUD

- [ ] 관리자가 공지사항을 작성할 수 있다.
- [ ] 부서관리자가 공지사항을 작성할 수 있다.
- [ ] 일반 사용자는 공지사항을 작성할 수 없다 (403 응답).
- [ ] 공지사항 목록을 조회할 수 있다 (페이지네이션 포함).
- [ ] 카테고리별로 공지사항을 필터링할 수 있다.
- [ ] 제목/내용으로 공지사항을 검색할 수 있다.
- [ ] 공지사항 상세를 조회할 수 있다.
- [ ] 작성자 본인이 공지사항을 수정할 수 있다.
- [ ] 관리자가 다른 사람의 공지사항을 수정할 수 있다.
- [ ] 삭제된 공지사항은 목록에 표시되지 않는다 (소프트 삭제).

### 7.2 상단 고정

- [ ] 고정된 공지는 목록 최상단에 표시된다.
- [ ] 고정 만료일이 지난 공지는 일반 목록으로 이동한다.
- [ ] 고정 만료일 없이 설정된 공지는 수동 해제 전까지 유지된다.

### 7.3 팝업 공지

- [ ] 팝업 기간 내 로그인 시 모달이 표시된다.
- [ ] "오늘 하루 보지 않기" 선택 후에는 당일 재표시되지 않는다.
- [ ] 팝업 기간 종료 후에는 모달이 표시되지 않는다.

### 7.4 필독 확인

- [ ] 필독 공지에서 "읽음 확인" 버튼을 클릭하면 읽음 기록이 저장된다.
- [ ] 이미 읽음 처리한 공지에 대해 중복 기록이 생성되지 않는다.
- [ ] 관리자가 읽음 현황(읽은 사람/안 읽은 사람)을 조회할 수 있다.
- [ ] 읽음률(퍼센트)이 정확히 계산된다.

### 7.5 조회수

- [ ] 상세 조회 시 조회수가 증가한다.
- [ ] 동일 사용자의 단시간 내 반복 조회는 중복 카운트되지 않는다.

## 8. 참고사항

- Rich Text 에디터는 **Tiptap** 또는 **Toast UI Editor**를 사용한다.
- 팝업 공지의 "오늘 하루 보지 않기" 상태는 클라이언트 측 localStorage에 저장한다 (키: `popup_dismissed_{notice_id}_{date}`).
- 조회수 중복 방지는 Redis에 `notice_view:{notice_id}:{user_id}` 키를 TTL 1시간으로 저장하여 처리한다.
- 고정 만료 및 팝업 기간 체크는 API 조회 시점에서 DB 쿼리로 처리한다 (별도 스케줄러 불필요).
- 첨부파일 및 댓글 기능은 `03-03` 공통 모듈을 사용한다.
