# Arontier 사내 그룹웨어 - 프로젝트 마스터 인덱스

## 1. 프로젝트 개요

Arontier(아론티어) 사내 업무 효율화를 위한 그룹웨어 시스템을 개발한다. 본 시스템은 인증/조직 관리, 전자결재, 게시판, 근태관리, 자산관리 5개 핵심 모듈로 구성되며, 한국 노동법 및 기업 문화에 맞춘 기능을 제공한다.

- **회사**: Arontier (서울 소재)
- **사용자**: 전 임직원
- **운영 환경**: 웹 브라우저 (데스크톱/모바일 반응형)

## 2. 기술 스택

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| 프론트엔드 | Next.js (App Router) | 14+ | React 기반 SSR/CSR 하이브리드 |
| UI 컴포넌트 | shadcn/ui | - | Radix UI + Tailwind CSS 기반 컴포넌트 라이브러리 |
| 백엔드 | Python FastAPI | 0.100+ | REST API 서버 |
| 데이터베이스 | PostgreSQL | 16+ | 관계형 데이터 저장소 |
| 캐시/세션 | Redis | 7+ | JWT 블랙리스트, 세션 캐시 |
| 파일 저장소 | 로컬 파일시스템 | - | 첨부파일, 프로필 이미지, 자산 이미지 |
| ORM | SQLAlchemy | 2.0+ | 데이터베이스 접근 |
| 마이그레이션 | Alembic | - | DB 스키마 버전 관리 |

## 3. 공통 설계 원칙

### 3.1 API 규칙

- **버전**: 모든 API는 `/api/v1/` 접두사 사용
- **인증**: JWT Bearer 토큰
  - Access Token: 30분 만료
  - Refresh Token: 7일 만료
- **Content-Type**: `application/json` (파일 업로드 시 `multipart/form-data`)

### 3.2 에러 응답 포맷

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {}
  }
}
```

공통 에러 코드:
| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| `VALIDATION_ERROR` | 400 | 요청 데이터 유효성 검증 실패 |
| `UNAUTHORIZED` | 401 | 인증 필요 |
| `FORBIDDEN` | 403 | 권한 없음 |
| `RESOURCE_NOT_FOUND` | 404 | 리소스 없음 |
| `CONFLICT` | 409 | 충돌 (중복 등) |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류 |

### 3.3 페이지네이션

Offset 기반 페이지네이션:

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "size": 20
}
```

- 기본 페이지 크기: 20
- 최대 페이지 크기: 100
- 쿼리 파라미터: `?page=1&size=20`

### 3.4 데이터베이스 공통 규칙

- **PK**: UUID v4 (`id` 컬럼)
- **Soft Delete**: `deleted_at TIMESTAMP NULL` (NULL이면 활성, 값이 있으면 삭제됨)
- **Audit 컬럼** (모든 테이블 공통):

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID | Primary Key (v4) |
| `created_by` | UUID | 생성자 (users.id FK) |
| `created_at` | TIMESTAMP | 생성 시각 (UTC) |
| `updated_by` | UUID | 수정자 (users.id FK) |
| `updated_at` | TIMESTAMP | 수정 시각 (UTC) |
| `deleted_at` | TIMESTAMP NULL | 삭제 시각 (soft delete) |

### 3.5 파일 저장소

로컬 파일시스템을 사용하며, `UPLOAD_DIR` 환경변수로 루트 경로를 설정한다.

```
{UPLOAD_DIR}/
├── profiles/{user_id}/            # 프로필 사진
│   └── {uuid}.{ext}
├── attachments/{type}/{id}/       # 첨부파일 (type: NOTICE/POST/APPROVAL)
│   └── {uuid}_{original_name}
├── thumbnails/{type}/{id}/        # 이미지 썸네일
│   └── {uuid}_thumb.{ext}
└── assets/{asset_id}/             # 자산 이미지
    └── {uuid}.{ext}
```

- 파일 다운로드는 서버 경유 API (`/api/v1/attachments/{id}/download`)로 제공
- 업로드 디렉토리는 웹 서버에서 직접 접근 불가하도록 설정
- 물리 삭제는 soft delete 후 30일 경과 시 배치 작업으로 처리

### 3.6 UI 컴포넌트 (shadcn/ui)

모든 프론트엔드 UI는 [shadcn/ui](https://ui.shadcn.com/) 컴포넌트를 기반으로 구현한다.

주요 사용 컴포넌트:
| 영역 | 컴포넌트 |
|------|----------|
| 레이아웃 | Sidebar, Tabs, Card, Sheet |
| 폼 | Input, Select, Checkbox, RadioGroup, DatePicker, Textarea, Form (react-hook-form 연동) |
| 테이블 | DataTable (TanStack Table 기반) |
| 피드백 | Dialog, AlertDialog, Toast (Sonner), Badge |
| 네비게이션 | Breadcrumb, Command (검색), DropdownMenu |
| 차트 | Charts (Recharts 기반 래퍼) |

### 3.7 타임존

- **DB 저장**: UTC
- **API 응답**: ISO 8601 형식 (`2026-03-23T09:00:00+09:00`)
- **표시 타임존**: Asia/Seoul (KST, UTC+9)

## 4. 모듈 의존성 그래프

```
Phase 1 (기반):
  01-01 인증 ──→ 01-02 사용자 관리 ──→ 01-03 조직도
                                    └──→ 01-04 역할/권한

Phase 2 (핵심 비즈니스 - 병렬 가능):
  02-01 결재 워크플로우  (← 01-03, 01-04)
  02-02 문서 양식        (← 02-01)
  03-01 공지사항         (← 01-04)
  03-03 첨부파일/댓글    (← 01-01)
  04-01 출퇴근           (← 01-03)

Phase 3 (확장 - 병렬 가능):
  02-03 결재 대시보드    (← 02-01, 02-02)
  03-02 팀 게시판        (← 01-03, 03-01)
  04-02 휴가 관리        (← 01-03, 02-01)
  04-03 초과근무         (← 04-01)
  05-01 자산 등록        (← 01-04)

Phase 4 (리포트):
  04-04 근태 리포트      (← 04-01, 04-02, 04-03)
  05-02 자산 배정        (← 05-01, 01-02, 01-03)
  05-03 자산 리포트      (← 05-01, 05-02)
```

## 5. 태스크 목록

| # | 파일 경로 | 제목 | 의존성 |
|---|-----------|------|--------|
| 1 | `01-auth-org/01-01-authentication.md` | 인증 (로그인/JWT/세션) | 없음 |
| 2 | `01-auth-org/01-02-user-management.md` | 사용자 관리 | 01-01 |
| 3 | `01-auth-org/01-03-org-chart.md` | 조직도 (부서/직급/직책) | 01-02 |
| 4 | `01-auth-org/01-04-role-permission.md` | 역할 및 권한 (RBAC) | 01-02 |
| 5 | `02-approval/02-01-approval-workflow.md` | 결재 워크플로우 | 01-03, 01-04 |
| 6 | `02-approval/02-02-document-templates.md` | 문서 양식 관리 | 02-01 |
| 7 | `02-approval/02-03-approval-dashboard.md` | 결재 대시보드 | 02-01, 02-02 |
| 8 | `03-board/03-01-notice-board.md` | 공지사항 게시판 | 01-04 |
| 9 | `03-board/03-02-team-board.md` | 부서/팀 게시판 | 01-03, 03-01 |
| 10 | `03-board/03-03-attachments-comments.md` | 첨부파일 및 댓글 (공통) | 01-01 |
| 11 | `04-attendance/04-01-check-in-out.md` | 출퇴근 관리 | 01-01, 01-03 |
| 12 | `04-attendance/04-02-leave-management.md` | 휴가 관리 | 01-03, 02-01 |
| 13 | `04-attendance/04-03-overtime.md` | 초과근무 관리 | 04-01 |
| 14 | `04-attendance/04-04-attendance-report.md` | 근태 현황 리포트 | 04-01, 04-02, 04-03 |
| 15 | `05-inventories/05-01-asset-registration.md` | 자산 등록 및 분류 | 01-04 |
| 16 | `05-inventories/05-02-asset-assignment.md` | 자산 배정 및 반납 | 05-01, 01-02, 01-03 |
| 17 | `05-inventories/05-03-asset-report.md` | 자산 현황 리포트 | 05-01, 05-02 |
