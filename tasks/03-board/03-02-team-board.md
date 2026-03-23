# 03-02 부서/팀 게시판

## 1. 개요

부서별 게시판과 전사 자유게시판을 제공하는 모듈이다. 부서 게시판은 해당 부서원만 접근할 수 있으며, 자유게시판은 전사 공용으로 운영된다. 관리자는 게시판을 생성/관리할 수 있고, 일반 사용자는 접근 가능한 게시판에서 게시글을 자유롭게 작성할 수 있다.

- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)
- **의존성**: `01-03` 조직도 (부서 정보), `01-04` 권한 관리 (게시판 관리 권한), `03-01` 공지사항 (게시판 패턴 참조)
- **관련 모듈**: `03-03` 첨부파일 및 댓글 (공통 모듈)

## 2. 기능 요구사항

### 2.1 게시판 관리

| 구분 | 설명 |
|------|------|
| 생성 | 관리자가 게시판을 생성한다. 게시판 유형, 이름, 설명, 연결 부서를 설정한다. |
| 수정 | 관리자가 게시판 정보를 수정한다. |
| 삭제 | 관리자가 게시판을 삭제(비활성화)한다. 게시글이 있는 게시판은 비활성화 처리한다. |
| 정렬 | 관리자가 게시판 표시 순서를 변경할 수 있다. |

### 2.2 게시판 유형

| 유형 | 코드 | 설명 |
|------|------|------|
| 부서 게시판 | DEPARTMENT | 특정 부서에 연결된 게시판. 해당 부서원만 접근 가능. |
| 자유게시판 | FREE | 전사 공용 게시판. 모든 사용자가 접근 가능. |
| 커스텀 게시판 | CUSTOM | 관리자가 용도에 맞게 생성한 게시판. 접근 권한을 별도 설정 가능. |

### 2.3 접근 권한

- **부서 게시판**: 해당 부서에 소속된 사용자만 목록 조회, 상세 조회, 작성이 가능하다.
- **자유게시판**: 모든 로그인 사용자가 접근 가능하다.
- **커스텀 게시판**: `board_permissions` 테이블을 통해 부서 또는 사용자 단위로 접근 권한을 제어한다.
- 관리자는 모든 게시판에 접근 가능하다.

### 2.4 게시글 CRUD

| 구분 | 설명 |
|------|------|
| 작성 | 접근 권한이 있는 사용자가 게시글을 작성한다. 제목, 내용(Rich Text), 첨부파일을 등록할 수 있다. |
| 조회 | 접근 권한이 있는 사용자가 게시글 목록 및 상세를 조회할 수 있다. |
| 수정 | 작성자 본인이 게시글을 수정할 수 있다. |
| 삭제 | 작성자 본인 또는 관리자가 게시글을 삭제(소프트 삭제)할 수 있다. |

### 2.5 게시글 상단 고정

- 게시판 관리자 또는 시스템 관리자가 특정 게시글을 상단에 고정할 수 있다.
- 고정된 게시글은 목록 최상단에 표시된다.

### 2.6 게시글 검색

- 검색 범위: 제목, 내용, 작성자
- 게시판 단위로 검색한다 (특정 게시판 내 검색).
- 전체 게시판 통합 검색은 추후 확장 시 지원한다.

### 2.7 페이지네이션

- 기본 페이지 크기: 20건
- 정렬: 최신순 (기본), 조회수순

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 게시글 목록 조회 API 응답 시간 500ms 이내 |
| 보안 | 부서 게시판 접근 시 소속 부서 검증 필수 |
| 데이터 보존 | 소프트 삭제 적용, 게시판 비활성화 시 게시글 보존 |
| 확장성 | 게시판 수 제한 없음. 대량 게시글(10만 건 이상) 처리 가능해야 함 |

## 4. 데이터베이스 스키마

### 4.1 boards (게시판)

```sql
CREATE TABLE boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,             -- 게시판 이름
    description VARCHAR(500),               -- 게시판 설명
    type VARCHAR(20) NOT NULL,              -- DEPARTMENT, FREE, CUSTOM
    department_id UUID REFERENCES departments(id),  -- 부서 게시판인 경우 연결 부서
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT chk_board_type CHECK (type IN ('DEPARTMENT', 'FREE', 'CUSTOM')),
    CONSTRAINT chk_department_board CHECK (
        (type = 'DEPARTMENT' AND department_id IS NOT NULL) OR
        (type != 'DEPARTMENT')
    )
);

CREATE INDEX idx_boards_type ON boards(type) WHERE deleted_at IS NULL;
CREATE INDEX idx_boards_department_id ON boards(department_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_boards_sort_order ON boards(sort_order) WHERE deleted_at IS NULL AND is_active = TRUE;
```

### 4.2 board_permissions (게시판 접근 권한 - 커스텀 게시판용)

```sql
CREATE TABLE board_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES boards(id),
    target_type VARCHAR(20) NOT NULL,       -- DEPARTMENT, USER
    target_id UUID NOT NULL,                -- department_id 또는 user_id
    permission VARCHAR(20) NOT NULL DEFAULT 'READ_WRITE',  -- READ, READ_WRITE
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_target_type CHECK (target_type IN ('DEPARTMENT', 'USER')),
    CONSTRAINT chk_permission CHECK (permission IN ('READ', 'READ_WRITE')),
    UNIQUE(board_id, target_type, target_id)
);

CREATE INDEX idx_board_permissions_board_id ON board_permissions(board_id);
CREATE INDEX idx_board_permissions_target ON board_permissions(target_type, target_id);
```

### 4.3 posts (게시글)

```sql
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES boards(id),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,                   -- Rich Text (HTML)
    author_id UUID NOT NULL REFERENCES users(id),
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    view_count INTEGER NOT NULL DEFAULT 0,
    comment_count INTEGER NOT NULL DEFAULT 0,  -- 비정규화: 댓글 수 캐시
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_posts_board_id ON posts(board_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_posts_board_created ON posts(board_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_posts_board_pinned ON posts(board_id, is_pinned) WHERE deleted_at IS NULL;
CREATE INDEX idx_posts_search ON posts USING gin(to_tsvector('korean', title || ' ' || content)) WHERE deleted_at IS NULL;
```

### ERD 요약

```
departments   1──1 boards (type=DEPARTMENT)
boards        1──N posts
boards        1──N board_permissions (type=CUSTOM)
users         1──N posts (author_id)
posts         1──N attachments (attachable_type='POST', 03-03 참조)
posts         1──N comments (commentable_type='POST', 03-03 참조)
```

## 5. API 명세

### 5.1 게시판 목록 조회

```
GET /api/v1/boards
```

**설명**: 현재 사용자가 접근 가능한 게시판 목록을 반환한다.

**쿼리 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| type | string | N | 게시판 유형 필터: DEPARTMENT, FREE, CUSTOM |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": [
    {
      "id": "board-uuid-001",
      "name": "자유게시판",
      "description": "전사 공용 자유게시판입니다.",
      "type": "FREE",
      "department": null,
      "post_count": 1234,
      "latest_post_at": "2026-03-23T08:00:00Z",
      "sort_order": 1
    },
    {
      "id": "board-uuid-002",
      "name": "개발팀 게시판",
      "description": "개발팀 내부 게시판",
      "type": "DEPARTMENT",
      "department": {
        "id": "dept-uuid-001",
        "name": "개발팀"
      },
      "post_count": 567,
      "latest_post_at": "2026-03-22T17:30:00Z",
      "sort_order": 2
    },
    {
      "id": "board-uuid-003",
      "name": "프로젝트 A 게시판",
      "description": "프로젝트 A 관련 공유 게시판",
      "type": "CUSTOM",
      "department": null,
      "post_count": 89,
      "latest_post_at": "2026-03-21T14:00:00Z",
      "sort_order": 3
    }
  ]
}
```

### 5.2 게시판 생성

```
POST /api/v1/boards
```

**권한**: 관리자

**요청 본문**

```json
{
  "name": "마케팅팀 게시판",
  "description": "마케팅팀 내부 소통 게시판",
  "type": "DEPARTMENT",
  "department_id": "dept-uuid-002",
  "sort_order": 5
}
```

**응답 (201 Created)**

```json
{
  "success": true,
  "data": {
    "id": "board-uuid-010",
    "name": "마케팅팀 게시판",
    "type": "DEPARTMENT",
    "created_at": "2026-03-23T10:00:00Z"
  }
}
```

### 5.3 게시판 수정

```
PUT /api/v1/boards/{boardId}
```

**권한**: 관리자

**요청 본문**

```json
{
  "name": "마케팅팀 게시판 (수정)",
  "description": "마케팅팀 내부 소통을 위한 공간입니다.",
  "is_active": true,
  "sort_order": 3
}
```

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": "board-uuid-010",
    "name": "마케팅팀 게시판 (수정)",
    "updated_at": "2026-03-23T11:00:00Z"
  }
}
```

### 5.4 게시판 삭제

```
DELETE /api/v1/boards/{boardId}
```

**권한**: 관리자

**설명**: 게시판을 비활성화(소프트 삭제)한다. 게시글은 보존된다.

**응답 (200 OK)**

```json
{
  "success": true,
  "message": "게시판이 삭제되었습니다."
}
```

### 5.5 게시글 목록 조회

```
GET /api/v1/boards/{boardId}/posts
```

**권한**: 해당 게시판 접근 권한이 있는 사용자

**쿼리 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | integer | N | 페이지 번호 (기본: 1) |
| size | integer | N | 페이지 크기 (기본: 20, 최대: 100) |
| sort | string | N | 정렬: latest (기본), views |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "board": {
      "id": "board-uuid-001",
      "name": "자유게시판",
      "type": "FREE"
    },
    "pinned": [
      {
        "id": "post-uuid-100",
        "title": "자유게시판 이용 규칙 안내",
        "author": {
          "id": "user-uuid-001",
          "name": "김관리",
          "department": "경영지원팀"
        },
        "is_pinned": true,
        "view_count": 890,
        "comment_count": 5,
        "has_attachment": false,
        "created_at": "2026-01-15T09:00:00Z"
      }
    ],
    "items": [
      {
        "id": "post-uuid-200",
        "title": "점심 맛집 추천합니다",
        "author": {
          "id": "user-uuid-050",
          "name": "박사원",
          "department": "개발팀"
        },
        "is_pinned": false,
        "view_count": 45,
        "comment_count": 12,
        "has_attachment": true,
        "created_at": "2026-03-23T07:30:00Z"
      },
      {
        "id": "post-uuid-201",
        "title": "사내 동호회 축구 모임",
        "author": {
          "id": "user-uuid-080",
          "name": "최사원",
          "department": "디자인팀"
        },
        "is_pinned": false,
        "view_count": 32,
        "comment_count": 8,
        "has_attachment": false,
        "created_at": "2026-03-22T16:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total_count": 1234,
      "total_pages": 62
    }
  }
}
```

### 5.6 게시글 검색

```
GET /api/v1/boards/{boardId}/posts/search
```

**쿼리 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| q | string | Y | 검색어 |
| search_type | string | N | 검색 유형: title, content, author, all (기본: all) |
| page | integer | N | 페이지 번호 (기본: 1) |
| size | integer | N | 페이지 크기 (기본: 20) |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "post-uuid-200",
        "title": "점심 맛집 추천합니다",
        "content_preview": "...회사 근처 <mark>맛집</mark>을 소개합니다...",
        "author": {
          "id": "user-uuid-050",
          "name": "박사원",
          "department": "개발팀"
        },
        "view_count": 45,
        "comment_count": 12,
        "created_at": "2026-03-23T07:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total_count": 3,
      "total_pages": 1
    }
  }
}
```

### 5.7 게시글 상세 조회

```
GET /api/v1/boards/{boardId}/posts/{postId}
```

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": "post-uuid-200",
    "board": {
      "id": "board-uuid-001",
      "name": "자유게시판"
    },
    "title": "점심 맛집 추천합니다",
    "content": "<p>회사 근처 맛집을 소개합니다.</p><p>1. 한식당 - 된장찌개가 맛있습니다.</p>",
    "author": {
      "id": "user-uuid-050",
      "name": "박사원",
      "department": "개발팀"
    },
    "is_pinned": false,
    "view_count": 46,
    "attachments": [
      {
        "id": "attach-uuid-001",
        "file_name": "맛집_지도.png",
        "file_size": 524288,
        "mime_type": "image/png",
        "thumbnail_path": "/thumbnails/attach-uuid-001.png"
      }
    ],
    "comments": [
      {
        "id": "comment-uuid-001",
        "content": "좋은 정보 감사합니다!",
        "author": {
          "id": "user-uuid-060",
          "name": "이사원",
          "department": "인사팀"
        },
        "parent_id": null,
        "created_at": "2026-03-23T08:00:00Z",
        "replies": [
          {
            "id": "comment-uuid-002",
            "content": "저도 가봤는데 진짜 맛있어요.",
            "author": {
              "id": "user-uuid-070",
              "name": "정사원",
              "department": "총무팀"
            },
            "parent_id": "comment-uuid-001",
            "created_at": "2026-03-23T08:30:00Z"
          }
        ]
      }
    ],
    "created_at": "2026-03-23T07:30:00Z",
    "updated_at": null
  }
}
```

### 5.8 게시글 작성

```
POST /api/v1/boards/{boardId}/posts
```

**권한**: 해당 게시판 접근 권한이 있는 사용자

**요청 본문**

```json
{
  "title": "이번 주 금요일 회식 안내",
  "content": "<p>이번 주 금요일에 팀 회식이 있습니다.</p><p>장소: 강남역 근처</p>",
  "attachment_ids": ["attach-uuid-010"]
}
```

**응답 (201 Created)**

```json
{
  "success": true,
  "data": {
    "id": "post-uuid-300",
    "title": "이번 주 금요일 회식 안내",
    "board_id": "board-uuid-001",
    "created_at": "2026-03-23T12:00:00Z"
  }
}
```

### 5.9 게시글 수정

```
PUT /api/v1/boards/{boardId}/posts/{postId}
```

**권한**: 작성자 본인

**요청 본문**

```json
{
  "title": "이번 주 금요일 회식 안내 (장소 변경)",
  "content": "<p>장소가 변경되었습니다.</p><p>변경 장소: 역삼역 근처</p>",
  "attachment_ids": ["attach-uuid-010", "attach-uuid-011"]
}
```

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": "post-uuid-300",
    "title": "이번 주 금요일 회식 안내 (장소 변경)",
    "updated_at": "2026-03-23T13:00:00Z"
  }
}
```

### 5.10 게시글 삭제

```
DELETE /api/v1/boards/{boardId}/posts/{postId}
```

**권한**: 작성자 본인 또는 관리자

**응답 (200 OK)**

```json
{
  "success": true,
  "message": "게시글이 삭제되었습니다."
}
```

### 5.11 에러 응답

| 에러 코드 | HTTP 상태 | 설명 |
|-----------|-----------|------|
| BOARD_NOT_FOUND | 404 | 게시판이 존재하지 않거나 비활성화됨 |
| BOARD_ACCESS_DENIED | 403 | 게시판 접근 권한 없음 |
| POST_NOT_FOUND | 404 | 게시글이 존재하지 않거나 삭제됨 |
| POST_FORBIDDEN | 403 | 게시글 수정/삭제 권한 없음 |
| BOARD_HAS_POSTS | 400 | 게시글이 있는 게시판은 물리 삭제 불가 |

## 6. 화면 설계

### 6.1 게시판 목록 사이드바

```
+---------------------------+
| 게시판                    |
+---------------------------+
| 📋 공지사항               |
+---------------------------+
| 전사 게시판               |
|   📝 자유게시판    (1234) |
+---------------------------+
| 내 부서 게시판            |
|   📁 개발팀 게시판  (567) |
+---------------------------+
| 프로젝트 게시판           |
|   📁 프로젝트 A     (89) |
|   📁 프로젝트 B     (45) |
+---------------------------+
| ⚙ 게시판 관리 (관리자)   |
+---------------------------+
```

- 사이드바에 접근 가능한 게시판이 유형별로 그룹화되어 표시된다.
- 각 게시판 옆에 게시글 수가 표시된다.
- 새 게시글이 있는 게시판은 별도 표시(볼드 또는 뱃지)한다.

### 6.2 게시글 목록 화면

```
+------------------------------------------------------------------+
| 자유게시판                                          [글 작성]     |
| 전사 공용 자유게시판입니다.                                        |
+------------------------------------------------------------------+
| 검색: [제목+내용 v] [검색어 입력...] [검색]                       |
+------------------------------------------------------------------+
| 번호 | 제목                          | 작성자 | 날짜   | 조회 | 댓글 |
+------+-------------------------------+--------+--------+------+------+
| 📌  | 자유게시판 이용 규칙 안내     | 김관리 | 01-15 | 890  |  5  |
+------+-------------------------------+--------+--------+------+------+
| 1234 | 점심 맛집 추천합니다 📎      | 박사원 | 03-23 |  45  | 12  |
| 1233 | 사내 동호회 축구 모임         | 최사원 | 03-22 |  32  |  8  |
| 1232 | 주말 등산 같이 가실 분?       | 이사원 | 03-22 |  28  |  6  |
| 1231 | 재택근무 팁 공유              | 정사원 | 03-21 |  56  | 15  |
| ...  | ...                           | ...    | ...    | ...  | ... |
+------+-------------------------------+--------+--------+------+------+
|                      < 1  2  3  ... 62 >                          |
+------------------------------------------------------------------+
```

- 고정 게시글은 상단에 배경색을 구분하여 표시한다.
- 첨부파일이 있는 게시글에는 클립 아이콘을 표시한다.
- 댓글 수가 0이 아닌 게시글에는 댓글 수를 표시한다.
- 새 게시글(24시간 이내)에는 "N" 뱃지를 표시한다.

### 6.3 게시글 상세 화면

```
+------------------------------------------------------------------+
| < 목록으로                                                        |
+------------------------------------------------------------------+
| 점심 맛집 추천합니다                                               |
| 작성자: 박사원 (개발팀) | 작성일: 2026-03-23 07:30 | 조회: 46    |
+------------------------------------------------------------------+
|                                                                    |
| 회사 근처 맛집을 소개합니다.                                       |
|                                                                    |
| 1. 한식당 - 된장찌개가 맛있습니다.                                 |
| 2. 일식당 - 초밥 런치 세트 추천                                    |
|                                                                    |
+------------------------------------------------------------------+
| 첨부파일                                                          |
| 📎 맛집_지도.png (512KB) [다운로드]  [미리보기]                   |
+------------------------------------------------------------------+
| 댓글 (12)                                                         |
| ┌─ 이사원 (인사팀) | 03-23 08:00                    [답글] [삭제] |
| │  좋은 정보 감사합니다!                                           |
| │  └─ 정사원 (총무팀) | 03-23 08:30                 [답글] [삭제] |
| │     저도 가봤는데 진짜 맛있어요.                                  |
| ├─ 김대리 (마케팅팀) | 03-23 09:00                  [답글] [삭제] |
| │  혹시 가격대는 어떤가요?                                         |
+------------------------------------------------------------------+
| 댓글 작성                                                         |
| [댓글 내용 입력...]                                    [등록]     |
+------------------------------------------------------------------+
|                           [수정] [삭제]  ※ 작성자/관리자만 표시   |
+------------------------------------------------------------------+
```

### 6.4 게시글 작성/수정 폼

```
+------------------------------------------------------------------+
| 글 작성 - 자유게시판                                               |
+------------------------------------------------------------------+
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
+------------------------------------------------------------------+
|                                              [취소]  [등록]       |
+------------------------------------------------------------------+
```

### 6.5 게시판 관리 화면 (관리자)

```
+------------------------------------------------------------------+
| 게시판 관리                                       [게시판 추가]   |
+------------------------------------------------------------------+
| 순서 | 이름              | 유형   | 연결 부서  | 상태   | 관리    |
+------+-------------------+--------+-----------+--------+---------+
|  1   | 자유게시판        | 전사   | -         | 활성   | [수정]  |
|  2   | 개발팀 게시판     | 부서   | 개발팀    | 활성   | [수정]  |
|  3   | 마케팅팀 게시판   | 부서   | 마케팅팀  | 활성   | [수정]  |
|  4   | 프로젝트 A 게시판 | 커스텀 | -         | 활성   | [수정]  |
|  5   | 구 총무 게시판    | 부서   | 총무팀    | 비활성 | [수정]  |
+------+-------------------+--------+-----------+--------+---------+
| ※ 드래그앤드롭으로 순서를 변경할 수 있습니다.                     |
+------------------------------------------------------------------+
```

## 7. 인수 조건

### 7.1 게시판 관리

- [ ] 관리자가 게시판을 생성할 수 있다 (부서, 자유, 커스텀 유형).
- [ ] 관리자가 게시판 정보를 수정할 수 있다.
- [ ] 관리자가 게시판을 비활성화할 수 있다.
- [ ] 비활성화된 게시판은 사이드바에서 숨겨진다.
- [ ] 일반 사용자는 게시판을 관리할 수 없다 (403 응답).
- [ ] 게시판 표시 순서를 변경할 수 있다.

### 7.2 접근 권한

- [ ] 부서 게시판은 해당 부서원만 접근할 수 있다.
- [ ] 다른 부서의 게시판에 접근하면 403 응답을 반환한다.
- [ ] 자유게시판은 모든 로그인 사용자가 접근할 수 있다.
- [ ] 커스텀 게시판은 권한이 설정된 부서/사용자만 접근할 수 있다.
- [ ] 관리자는 모든 게시판에 접근할 수 있다.

### 7.3 게시글 CRUD

- [ ] 접근 권한이 있는 사용자가 게시글을 작성할 수 있다.
- [ ] 게시글 목록을 조회할 수 있다 (페이지네이션 포함).
- [ ] 고정 게시글이 목록 최상단에 표시된다.
- [ ] 게시글 상세를 조회할 수 있다.
- [ ] 작성자 본인이 게시글을 수정할 수 있다.
- [ ] 작성자 본인 또는 관리자가 게시글을 삭제할 수 있다.
- [ ] 삭제된 게시글은 목록에 표시되지 않는다.

### 7.4 게시글 검색

- [ ] 제목으로 게시글을 검색할 수 있다.
- [ ] 내용으로 게시글을 검색할 수 있다.
- [ ] 작성자로 게시글을 검색할 수 있다.
- [ ] 검색 결과에 검색어 하이라이트가 표시된다.

### 7.5 조회수

- [ ] 게시글 상세 조회 시 조회수가 증가한다.

## 8. 참고사항

- 부서 게시판 접근 권한 확인 시 `01-03` 조직도 모듈의 부서 소속 정보를 활용한다.
- 커스텀 게시판 생성 시 `board_permissions`에 접근 권한을 함께 설정한다.
- 게시글의 `comment_count`는 댓글 생성/삭제 시 트리거 또는 애플리케이션 레벨에서 갱신한다.
- 게시판 사이드바 목록은 클라이언트 측에서 캐싱하고, 게시판 변경 시 갱신한다.
- 게시판 순서 변경은 드래그앤드롭 UI를 지원하며, PATCH `/api/v1/boards/reorder` API로 일괄 변경한다.
- 첨부파일 및 댓글 기능은 `03-03` 공통 모듈을 사용한다.
- 부서 게시판은 조직도에서 부서가 생성될 때 자동 생성하는 것도 고려할 수 있으나, 초기 버전에서는 관리자가 수동 생성한다.
