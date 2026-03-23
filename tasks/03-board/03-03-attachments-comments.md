# 03-03 첨부파일 및 댓글 (공통 모듈)

## 1. 개요

게시판, 전자결재 등 여러 모듈에서 공통으로 사용하는 첨부파일 업로드/다운로드 및 댓글/대댓글 기능을 제공하는 모듈이다. Polymorphic 연관 방식을 사용하여 다양한 엔티티에 유연하게 연결할 수 있다.

- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스) + 로컬 파일시스템
- **의존성**: 없음 (공통 모듈로서 다른 모듈이 이 모듈에 의존)
- **사용처**: `03-01` 공지사항, `03-02` 부서/팀 게시판, 향후 전자결재 등

## 2. 기능 요구사항

### 2.1 첨부파일

#### 2.1.1 파일 업로드

| 항목 | 설명 |
|------|------|
| 전송 방식 | `multipart/form-data` |
| 저장소 | 로컬 파일시스템 (`{UPLOAD_DIR}/attachments/`) |
| 크기 제한 | 파일당 최대 50MB |
| 총량 제한 | 게시글(엔티티)당 총 200MB |
| 파일명 처리 | UUID prefix를 붙여 중복 방지 (예: `a1b2c3d4_원본파일명.pdf`) |

#### 2.1.2 허용 확장자

| 분류 | 확장자 |
|------|--------|
| 문서 | pdf, doc, docx, xls, xlsx, ppt, pptx, hwp |
| 이미지 | jpg, jpeg, png, gif |
| 압축 | zip, tar.gz |

허용되지 않은 확장자의 파일은 업로드를 거부한다.

#### 2.1.3 파일 다운로드

- 원본 파일명으로 다운로드한다 (`Content-Disposition` 헤더 설정).
- 서버 경유 다운로드 API (`/api/v1/attachments/{id}/download`)를 통해 파일을 제공한다.
- 다운로드 권한은 해당 엔티티 접근 권한과 동일하게 적용한다.

#### 2.1.4 이미지 썸네일

- 이미지 파일(jpg, jpeg, png, gif) 업로드 시 썸네일을 자동 생성한다.
- 썸네일 크기: 최대 200x200px (비율 유지).
- 썸네일은 로컬 파일시스템의 별도 경로(`{UPLOAD_DIR}/thumbnails/`)에 저장한다.
- 게시글 목록이나 첨부파일 미리보기에서 썸네일을 사용한다.

#### 2.1.5 파일 삭제

- 업로드한 본인 또는 관리자만 삭제할 수 있다.
- 소프트 삭제 적용 (DB의 `deleted_at` 설정, 로컬 파일은 보존).
- 로컬 파일의 물리 삭제는 배치 작업으로 별도 처리한다 (소프트 삭제 후 30일 경과 시).

### 2.2 댓글/대댓글

#### 2.2.1 댓글 CRUD

| 구분 | 설명 |
|------|------|
| 작성 | 해당 엔티티 접근 권한이 있는 사용자가 댓글을 작성한다. |
| 조회 | 엔티티 상세 조회 시 댓글 목록을 함께 반환한다. |
| 수정 | 작성자 본인만 댓글을 수정할 수 있다. |
| 삭제 | 작성자 본인만 댓글을 삭제할 수 있다. 대댓글이 있는 댓글은 내용을 "삭제된 댓글입니다."로 대체한다. |

#### 2.2.2 대댓글

- 댓글에 대한 답글(대댓글)을 작성할 수 있다.
- 대댓글 깊이는 **1단계까지만** 허용한다 (댓글 → 대댓글, 대댓글에 대한 대댓글은 불가).
- 대댓글은 `parent_id`로 상위 댓글을 참조한다.

#### 2.2.3 Polymorphic 연관

- `commentable_type`과 `commentable_id`를 사용하여 다양한 엔티티에 댓글을 연결한다.
- 현재 지원 타입: `NOTICE` (공지사항), `POST` (게시글)
- 향후 확장 시 타입만 추가하면 된다.

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 파일 업로드 시 서버 메모리 사용 최소화 (스트리밍 업로드) |
| 보안 | 파일 확장자 및 MIME 타입 이중 검증 (확장자 변조 방지) |
| 보안 | 업로드 디렉토리는 웹 서버에서 직접 접근 불가, API 경유로만 다운로드 |
| 가용성 | 디스크 용량 모니터링, 부족 시 업로드 실패를 명확히 사용자에게 알림 |
| 데이터 보존 | 소프트 삭제 적용, 로컬 파일 물리 삭제는 30일 보관 후 배치 처리 |
| 확장성 | 새로운 attachable_type / commentable_type 추가 시 코드 변경 최소화 |

## 4. 데이터베이스 스키마

### 4.1 attachments (첨부파일)

```sql
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attachable_type VARCHAR(20) NOT NULL,    -- NOTICE, POST, APPROVAL
    attachable_id UUID NOT NULL,             -- 연결된 엔티티 ID
    file_name VARCHAR(255) NOT NULL,         -- 원본 파일명
    file_path VARCHAR(500) NOT NULL,         -- 로컬 저장 경로 (UPLOAD_DIR 상대 경로)
    file_size BIGINT NOT NULL,               -- 파일 크기 (bytes)
    mime_type VARCHAR(100) NOT NULL,         -- MIME 타입
    file_extension VARCHAR(20) NOT NULL,     -- 파일 확장자
    thumbnail_path VARCHAR(500),             -- 썸네일 저장 경로 (이미지인 경우)
    uploaded_by UUID NOT NULL REFERENCES users(id),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT chk_attachable_type CHECK (attachable_type IN ('NOTICE', 'POST', 'APPROVAL'))
);

CREATE INDEX idx_attachments_attachable ON attachments(attachable_type, attachable_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_attachments_uploaded_by ON attachments(uploaded_by);
```

### 4.2 comments (댓글)

```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commentable_type VARCHAR(20) NOT NULL,   -- NOTICE, POST
    commentable_id UUID NOT NULL,            -- 연결된 엔티티 ID
    parent_id UUID REFERENCES comments(id),  -- 대댓글인 경우 상위 댓글 ID
    content TEXT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,  -- 대댓글이 있는 댓글 삭제 시 TRUE
    author_id UUID NOT NULL REFERENCES users(id),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT chk_commentable_type CHECK (commentable_type IN ('NOTICE', 'POST')),
    CONSTRAINT chk_reply_depth CHECK (
        parent_id IS NULL OR NOT EXISTS (
            SELECT 1 FROM comments c WHERE c.id = parent_id AND c.parent_id IS NOT NULL
        )
    )
);

CREATE INDEX idx_comments_commentable ON comments(commentable_type, commentable_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_parent_id ON comments(parent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_author_id ON comments(author_id);
```

> **참고**: 대댓글 깊이 제한(`chk_reply_depth`)은 CHECK 제약 조건의 서브쿼리 지원이 제한적인 경우 애플리케이션 레벨에서 검증한다.

### ERD 요약

```
notices     1──N attachments (attachable_type='NOTICE')
posts       1──N attachments (attachable_type='POST')
approvals   1──N attachments (attachable_type='APPROVAL', 향후)

notices     1──N comments (commentable_type='NOTICE')
posts       1──N comments (commentable_type='POST')

comments    1──N comments (parent_id, 대댓글)

users       1──N attachments (uploaded_by)
users       1──N comments (author_id)
```

### 4.3 로컬 저장소 구조

```
{UPLOAD_DIR}/
├── attachments/
│   ├── NOTICE/
│   │   └── {notice_id}/
│   │       ├── a1b2c3d4_공지첨부파일.pdf
│   │       └── e5f6g7h8_참고자료.docx
│   ├── POST/
│   │   └── {post_id}/
│   │       └── i9j0k1l2_맛집_지도.png
│   └── APPROVAL/
│       └── {approval_id}/
│           └── m3n4o5p6_결재서류.pdf
└── thumbnails/
    ├── NOTICE/
    │   └── {notice_id}/
    │       └── a1b2c3d4_thumb.png
    └── POST/
        └── {post_id}/
            └── i9j0k1l2_thumb.png
```

- `UPLOAD_DIR` 환경변수로 루트 경로 설정 (예: `/data/uploads`)
- 업로드 디렉토리는 웹 서버(Nginx 등)에서 직접 접근 불가하도록 설정

## 5. API 명세

### 5.1 파일 업로드

```
POST /api/v1/attachments
```

**Content-Type**: `multipart/form-data`

**요청 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| file | file | Y | 업로드할 파일 |
| attachable_type | string | Y | 연결 엔티티 타입: NOTICE, POST, APPROVAL |
| attachable_id | string | Y | 연결 엔티티 ID (UUID) |

**응답 (201 Created)**

```json
{
  "success": true,
  "data": {
    "id": "attach-uuid-001",
    "file_name": "3월_교육일정.pdf",
    "file_size": 1048576,
    "mime_type": "application/pdf",
    "file_extension": "pdf",
    "thumbnail_path": null,
    "created_at": "2026-03-23T10:00:00Z"
  }
}
```

**이미지 업로드 시 응답**

```json
{
  "success": true,
  "data": {
    "id": "attach-uuid-002",
    "file_name": "맛집_지도.png",
    "file_size": 524288,
    "mime_type": "image/png",
    "file_extension": "png",
    "thumbnail_path": "/thumbnails/POST/post-uuid-200/i9j0k1l2_thumb.png",
    "created_at": "2026-03-23T10:05:00Z"
  }
}
```

### 5.2 파일 다운로드

```
GET /api/v1/attachments/{id}/download
```

**설명**: 서버에서 로컬 파일을 읽어 스트리밍 응답으로 제공한다.

**응답 (200 OK)** - 파일 바이너리 스트리밍

```
Content-Type: application/pdf
Content-Disposition: attachment; filename="3월_교육일정.pdf"
Content-Length: 1048576
```

### 5.3 첨부파일 목록 조회

```
GET /api/v1/attachments
```

**쿼리 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| attachable_type | string | Y | 연결 엔티티 타입 |
| attachable_id | string | Y | 연결 엔티티 ID |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": [
    {
      "id": "attach-uuid-001",
      "file_name": "3월_교육일정.pdf",
      "file_size": 1048576,
      "mime_type": "application/pdf",
      "file_extension": "pdf",
      "thumbnail_path": null,
      "uploaded_by": {
        "id": "user-uuid-001",
        "name": "이인사"
      },
      "created_at": "2026-03-23T10:00:00Z"
    },
    {
      "id": "attach-uuid-002",
      "file_name": "교육장_안내도.png",
      "file_size": 262144,
      "mime_type": "image/png",
      "file_extension": "png",
      "thumbnail_path": "/thumbnails/NOTICE/notice-uuid/thumb.png",
      "uploaded_by": {
        "id": "user-uuid-001",
        "name": "이인사"
      },
      "created_at": "2026-03-23T10:05:00Z"
    }
  ]
}
```

### 5.4 파일 삭제

```
DELETE /api/v1/attachments/{id}
```

**권한**: 업로드한 본인 또는 관리자

**응답 (200 OK)**

```json
{
  "success": true,
  "message": "첨부파일이 삭제되었습니다."
}
```

### 5.5 댓글 목록 조회

```
GET /api/v1/{resourceType}/{resourceId}/comments
```

**경로 파라미터**

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| resourceType | 리소스 타입 | notices, posts |
| resourceId | 리소스 ID | UUID |

**쿼리 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | integer | N | 페이지 번호 (기본: 1) |
| size | integer | N | 페이지 크기 (기본: 50) |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "comment-uuid-001",
        "content": "교육 장소가 어디인가요?",
        "author": {
          "id": "user-uuid-050",
          "name": "박사원",
          "department": "개발팀"
        },
        "parent_id": null,
        "is_deleted": false,
        "created_at": "2026-03-22T15:00:00Z",
        "updated_at": null,
        "replies": [
          {
            "id": "comment-uuid-002",
            "content": "본관 3층 대회의실입니다.",
            "author": {
              "id": "user-uuid-001",
              "name": "이인사",
              "department": "인사팀"
            },
            "parent_id": "comment-uuid-001",
            "is_deleted": false,
            "created_at": "2026-03-22T15:30:00Z",
            "updated_at": null
          }
        ]
      },
      {
        "id": "comment-uuid-003",
        "content": "삭제된 댓글입니다.",
        "author": {
          "id": "user-uuid-060",
          "name": "최사원",
          "department": "디자인팀"
        },
        "parent_id": null,
        "is_deleted": true,
        "created_at": "2026-03-22T16:00:00Z",
        "updated_at": null,
        "replies": [
          {
            "id": "comment-uuid-004",
            "content": "답글이 있어서 삭제 표시만 됩니다.",
            "author": {
              "id": "user-uuid-070",
              "name": "정사원",
              "department": "총무팀"
            },
            "parent_id": "comment-uuid-003",
            "is_deleted": false,
            "created_at": "2026-03-22T16:30:00Z",
            "updated_at": null
          }
        ]
      }
    ],
    "total_count": 15
  }
}
```

### 5.6 댓글 작성

```
POST /api/v1/{resourceType}/{resourceId}/comments
```

**요청 본문 - 댓글**

```json
{
  "content": "좋은 정보 감사합니다!"
}
```

**요청 본문 - 대댓글**

```json
{
  "content": "저도 동의합니다.",
  "parent_id": "comment-uuid-001"
}
```

**응답 (201 Created)**

```json
{
  "success": true,
  "data": {
    "id": "comment-uuid-010",
    "content": "좋은 정보 감사합니다!",
    "author": {
      "id": "user-uuid-080",
      "name": "한사원",
      "department": "경영지원팀"
    },
    "parent_id": null,
    "created_at": "2026-03-23T11:00:00Z"
  }
}
```

### 5.7 댓글 수정

```
PUT /api/v1/{resourceType}/{resourceId}/comments/{commentId}
```

**권한**: 작성자 본인

**요청 본문**

```json
{
  "content": "수정된 댓글 내용입니다."
}
```

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": "comment-uuid-010",
    "content": "수정된 댓글 내용입니다.",
    "updated_at": "2026-03-23T11:30:00Z"
  }
}
```

### 5.8 댓글 삭제

```
DELETE /api/v1/{resourceType}/{resourceId}/comments/{commentId}
```

**권한**: 작성자 본인

**삭제 로직**:
- 대댓글이 없는 댓글: 소프트 삭제 (`deleted_at` 설정)
- 대댓글이 있는 댓글: `is_deleted = TRUE`, 내용을 "삭제된 댓글입니다."로 대체 (대댓글 보존)

**응답 (200 OK)**

```json
{
  "success": true,
  "message": "댓글이 삭제되었습니다."
}
```

### 5.9 에러 응답

| 에러 코드 | HTTP 상태 | 설명 |
|-----------|-----------|------|
| ATTACHMENT_NOT_FOUND | 404 | 첨부파일이 존재하지 않거나 삭제됨 |
| ATTACHMENT_FORBIDDEN | 403 | 첨부파일 삭제 권한 없음 |
| ATTACHMENT_SIZE_EXCEEDED | 400 | 파일 크기 제한 초과 (50MB) |
| ATTACHMENT_TOTAL_SIZE_EXCEEDED | 400 | 엔티티당 총 첨부파일 크기 제한 초과 (200MB) |
| ATTACHMENT_INVALID_EXTENSION | 400 | 허용되지 않은 파일 확장자 |
| ATTACHMENT_INVALID_MIME_TYPE | 400 | MIME 타입과 확장자 불일치 |
| COMMENT_NOT_FOUND | 404 | 댓글이 존재하지 않거나 삭제됨 |
| COMMENT_FORBIDDEN | 403 | 댓글 수정/삭제 권한 없음 |
| COMMENT_REPLY_DEPTH_EXCEEDED | 400 | 대댓글에 대한 대댓글 불가 (깊이 1 초과) |
| COMMENT_INVALID_PARENT | 400 | parent_id가 다른 엔티티의 댓글을 참조 |

## 6. 화면 설계

### 6.1 파일 업로드 컴포넌트

```
+------------------------------------------------------------------+
| 첨부파일                                                          |
+------------------------------------------------------------------+
| +--------------------------------------------------------------+ |
| |                                                              | |
| |     📂 파일을 드래그하여 놓거나 클릭하여 업로드하세요        | |
| |                                                              | |
| |     파일당 최대 50MB | 총 200MB                              | |
| |     허용: pdf, doc, docx, xls, xlsx, ppt, pptx,             | |
| |           hwp, jpg, png, gif, zip, tar.gz                    | |
| |                                                              | |
| +--------------------------------------------------------------+ |
|                                                                    |
| 업로드된 파일 (2개, 1.5MB / 200MB)                                |
| ┌────────────────────────────────────────────────────────────┐   |
| │ 📄 3월_교육일정.pdf          1.0MB  업로드 완료    [X]     │   |
| │ 🖼️ 교육장_안내도.png [미리보기] 512KB  업로드 완료    [X]  │   |
| └────────────────────────────────────────────────────────────┘   |
|                                                                    |
| 업로드 중                                                         |
| ┌────────────────────────────────────────────────────────────┐   |
| │ 📄 참고자료.docx    ████████████░░░░░░  75%    [취소]      │   |
| └────────────────────────────────────────────────────────────┘   |
+------------------------------------------------------------------+
```

- 드래그앤드롭 영역은 파일 호버 시 테두리 색상이 변경된다.
- 업로드 진행률을 프로그레스 바로 표시한다.
- 이미지 파일은 썸네일 미리보기를 제공한다.
- 파일별 삭제 버튼(X)으로 개별 삭제할 수 있다.
- 허용되지 않은 파일 드롭 시 에러 메시지를 표시한다.
- 크기 제한 초과 시 즉시 경고를 표시한다.

### 6.2 첨부파일 목록 (게시글 상세 내)

```
+------------------------------------------------------------------+
| 첨부파일 (2)                                                      |
+------------------------------------------------------------------+
| 📄 3월_교육일정.pdf (1.0MB)                        [다운로드]    |
| 🖼️ 교육장_안내도.png (512KB)          [미리보기]   [다운로드]    |
+------------------------------------------------------------------+
```

- 이미지 파일은 "미리보기" 버튼을 제공하여 모달로 원본 이미지를 표시한다.
- 다운로드 클릭 시 서버 API를 통해 파일을 다운로드한다.
- 파일 아이콘은 확장자에 따라 다른 아이콘을 표시한다.

### 6.3 이미지 미리보기 모달

```
+----------------------------------------------+
|                                        [X]   |
+----------------------------------------------+
|                                              |
|          +------------------------+          |
|          |                        |          |
|          |    (원본 이미지)       |          |
|          |                        |          |
|          +------------------------+          |
|                                              |
| 교육장_안내도.png (512KB)                    |
|                              [다운로드]      |
+----------------------------------------------+
```

### 6.4 댓글 섹션

```
+------------------------------------------------------------------+
| 댓글 (15)                                                         |
+------------------------------------------------------------------+
| 댓글 작성                                                         |
| +--------------------------------------------------------------+ |
| | [댓글 내용을 입력하세요...]                                   | |
| +--------------------------------------------------------------+ |
|                                                        [등록]     |
+------------------------------------------------------------------+
|                                                                    |
| 👤 박사원 (개발팀)                      2026-03-22 15:00  [답글] |
| 교육 장소가 어디인가요?                              [수정][삭제] |
|                                                                    |
|    ↳ 👤 이인사 (인사팀)                 2026-03-22 15:30  [답글] |
|      본관 3층 대회의실입니다.                         [수정][삭제] |
|                                                                    |
|    ↳ 👤 정사원 (총무팀)                 2026-03-22 16:00         |
|      감사합니다. 확인했습니다.                        [수정][삭제] |
|                                                                    |
| ─────────────────────────────────────────────────────────────── |
|                                                                    |
| 👤 최사원 (디자인팀)                    2026-03-22 16:00         |
| [삭제된 댓글입니다.]                                              |
|                                                                    |
|    ↳ 👤 한사원 (경영지원팀)             2026-03-22 16:30  [답글] |
|      답글은 남아있습니다.                             [수정][삭제] |
|                                                                    |
+------------------------------------------------------------------+
| 더 보기 (5건 남음)                                                |
+------------------------------------------------------------------+
```

- 대댓글은 들여쓰기(인덴트)로 구분한다.
- "답글" 클릭 시 해당 댓글 하단에 답글 입력 폼이 나타난다.
- "수정"/"삭제" 버튼은 작성자 본인에게만 표시한다.
- 삭제된 댓글은 회색 텍스트로 "삭제된 댓글입니다." 표시하고, 대댓글은 그대로 유지한다.
- 댓글이 많은 경우 "더 보기" 버튼으로 추가 로딩한다.

### 6.5 답글 작성 인라인 폼

```
| 👤 박사원 (개발팀)                      2026-03-22 15:00  [답글] |
| 교육 장소가 어디인가요?                                          |
|                                                                    |
|    ┌──────────────────────────────────────────────────────────┐ |
|    │ @박사원 에게 답글 작성                                    │ |
|    │ [답글 내용을 입력하세요...]                                │ |
|    │                                          [취소] [등록]    │ |
|    └──────────────────────────────────────────────────────────┘ |
```

## 7. 인수 조건

### 7.1 파일 업로드

- [ ] `multipart/form-data` 형식으로 파일을 업로드할 수 있다.
- [ ] 업로드된 파일이 로컬 파일시스템에 저장된다.
- [ ] 파일명 중복 시 UUID prefix로 구분된다.
- [ ] 50MB 초과 파일 업로드 시 400 에러를 반환한다.
- [ ] 엔티티당 총 200MB 초과 시 400 에러를 반환한다.
- [ ] 허용되지 않은 확장자 파일 업로드 시 400 에러를 반환한다.
- [ ] 확장자와 MIME 타입이 불일치하면 업로드를 거부한다.
- [ ] 이미지 파일 업로드 시 썸네일이 자동 생성된다.
- [ ] 썸네일 크기가 최대 200x200px 이내이다.

### 7.2 파일 다운로드

- [ ] 서버 API를 통해 파일을 다운로드할 수 있다.
- [ ] 원본 파일명으로 다운로드된다.
- [ ] 해당 엔티티 접근 권한이 없으면 다운로드할 수 없다.

### 7.3 파일 삭제

- [ ] 업로드한 본인이 파일을 삭제할 수 있다.
- [ ] 관리자가 파일을 삭제할 수 있다.
- [ ] 다른 사용자는 파일을 삭제할 수 없다 (403 응답).
- [ ] 삭제 후에도 로컬 파일은 즉시 삭제되지 않는다 (소프트 삭제).

### 7.4 댓글 CRUD

- [ ] 엔티티 접근 권한이 있는 사용자가 댓글을 작성할 수 있다.
- [ ] 댓글 목록이 생성일 오름차순으로 표시된다.
- [ ] 작성자 본인이 댓글을 수정할 수 있다.
- [ ] 작성자 본인이 댓글을 삭제할 수 있다.
- [ ] 다른 사용자는 댓글을 수정/삭제할 수 없다 (403 응답).

### 7.5 대댓글

- [ ] 댓글에 대댓글을 작성할 수 있다.
- [ ] 대댓글이 상위 댓글 하단에 들여쓰기되어 표시된다.
- [ ] 대댓글에 대한 대댓글은 작성할 수 없다 (400 응답).
- [ ] 대댓글이 있는 댓글을 삭제하면 "삭제된 댓글입니다."로 표시되고 대댓글은 유지된다.
- [ ] 대댓글이 없는 댓글을 삭제하면 목록에서 제거된다.

### 7.6 Polymorphic 연관

- [ ] NOTICE 타입으로 첨부파일/댓글을 연결할 수 있다.
- [ ] POST 타입으로 첨부파일/댓글을 연결할 수 있다.
- [ ] 다른 엔티티의 첨부파일/댓글은 조회되지 않는다.

## 8. 참고사항

- **파일 저장소 설정**: 환경변수로 관리한다.
  - `UPLOAD_DIR`: 파일 저장 루트 경로 (예: `/data/uploads`)
  - `MAX_FILE_SIZE`: 파일당 최대 크기 (기본: 50MB)
  - `MAX_TOTAL_SIZE`: 엔티티당 최대 총 크기 (기본: 200MB)
- **썸네일 생성**: Python의 `Pillow` 라이브러리를 사용한다. 업로드 시 동기 처리하되, 대용량 이미지의 경우 비동기 작업 큐(Celery 등)로 전환을 고려한다.
- **파일 다운로드**: FastAPI의 `FileResponse` 또는 `StreamingResponse`를 사용하여 서버에서 파일을 직접 제공한다.
- **파일 바이러스 검사**: 초기 버전에서는 미구현. 추후 ClamAV 연동을 고려한다.
- **프론트엔드 업로드 컴포넌트**: shadcn/ui 기반 커스텀 드래그앤드롭 업로드 컴포넌트를 구현한다.
- **대용량 파일 업로드**: 초기 버전에서는 단일 업로드를 사용하며, 필요 시 청크 업로드로 전환한다.
- **디스크 용량 관리**: 업로드 전 디스크 잔여 용량을 확인하고, 임계치 이하 시 업로드를 거부한다.
- **댓글 실시간 갱신**: 초기 버전에서는 미구현. 추후 WebSocket 또는 SSE를 활용한 실시간 댓글 알림을 고려한다.
- **댓글 멘션**: 대댓글 작성 시 `@사용자명` 형태의 멘션을 표시하되, 초기 버전에서는 단순 텍스트로 처리한다. 추후 알림 연동을 고려한다.
