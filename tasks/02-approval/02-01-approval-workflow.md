# 02-01 결재 워크플로우

## 1. 개요

전자결재는 한국 기업 그룹웨어의 핵심 모듈로, 업무 문서의 기안부터 최종 승인까지의 결재 프로세스를 전자화한다. 기안자가 문서를 작성하고 결재선을 설정하여 상신하면, 결재자들이 순차 또는 병렬로 승인/반려를 처리한다.

### 선행 의존성
- [01-03 조직도](../01-auth-org/01-03-org-chart.md) - 결재선에서 조직도 기반 결재자 선택
- [01-04 역할/권한](../01-auth-org/01-04-role-permission.md) - 결재 관련 권한 제어

## 2. 기능 요구사항

### 2.1 기안 (문서 작성)
- [ ] 양식 선택 후 문서 내용 작성
- [ ] 임시저장 기능 (DRAFT 상태)
- [ ] 결재선 설정 (결재자/합의자/참조자 지정)
- [ ] 상신 (SUBMITTED 상태로 전환)
- [ ] 상신 취소 (첫 결재자 처리 전에만 가능)

### 2.2 결재선 설정
- [ ] 순차결재 (SEQUENTIAL): 결재자가 순서대로 한 명씩 처리
- [ ] 병렬결재 (PARALLEL): 해당 단계의 모든 결재자가 동시에 처리
- [ ] 합의 (AGREEMENT): 참조성 결재 (거부권 없음, 의견만 제출)
- [ ] 결재선 저장 (자주 사용하는 결재선 저장/불러오기)
- [ ] 조직도에서 결재자 검색 및 선택

### 2.3 결재 처리
- [ ] 승인 (APPROVE): 의견 입력 (선택)
- [ ] 반려 (REJECT): 반려 사유 필수 입력
- [ ] 보류 (HOLD): 보류 사유 입력
- [ ] 전결 (PRE_APPROVE): 상위자가 하위 결재를 사전에 위임
- [ ] 대결 (PROXY_APPROVE): 부재 시 지정된 대리인이 결재
- [ ] 후결 (POST_APPROVE): 긴급 시 사후 승인 처리

### 2.4 문서 상태 흐름
```
DRAFT(임시저장) → SUBMITTED(상신) → IN_PROGRESS(결재중) → APPROVED(승인완료)
                                                       → REJECTED(반려)
                  CANCELLED(취소) ← SUBMITTED(상신 취소)
```

### 2.5 알림
- [ ] 결재 요청 알림 (다음 결재자에게)
- [ ] 결재 완료 알림 (기안자에게)
- [ ] 반려 알림 (기안자에게)
- [ ] 참조 알림 (참조자에게)
- [ ] 인앱 알림 + 이메일 알림

## 3. 비기능 요구사항

- 결재 처리 응답 시간: 1초 이내
- 동시 결재 처리 시 낙관적 잠금(Optimistic Locking) 적용
- 결재 이력은 영구 보존 (삭제 불가)
- 결재 문서 내용 변경 시 변경 이력 추적

## 4. 데이터베이스 스키마

### 4.1 approval_documents (결재 문서)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 문서 ID |
| document_number | VARCHAR(30) | UNIQUE, NOT NULL | 문서번호 (자동 채번: APR-2026-00001) |
| template_id | UUID | FK → document_templates | 양식 ID |
| title | VARCHAR(200) | NOT NULL | 문서 제목 |
| content_json | JSONB | NOT NULL | 양식 필드별 입력 값 |
| status | VARCHAR(20) | NOT NULL | DRAFT/SUBMITTED/IN_PROGRESS/APPROVED/REJECTED/CANCELLED |
| urgency | VARCHAR(10) | DEFAULT 'NORMAL' | NORMAL/URGENT/EMERGENCY |
| submitted_by | UUID | FK → users | 기안자 |
| submitted_at | TIMESTAMP | NULL | 상신 일시 |
| completed_at | TIMESTAMP | NULL | 최종 처리 일시 |
| version | INTEGER | DEFAULT 1 | 낙관적 잠금용 버전 |
| created_by | UUID | FK → users | 생성자 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_by | UUID | FK → users | 수정자 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |
| deleted_at | TIMESTAMP | NULL | 삭제 시각 |

### 4.2 approval_lines (결재선)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 결재선 ID |
| document_id | UUID | FK → approval_documents | 문서 ID |
| approver_id | UUID | FK → users | 결재자 |
| proxy_approver_id | UUID | FK → users, NULL | 대결자 |
| step_order | INTEGER | NOT NULL | 결재 순서 (1부터) |
| line_type | VARCHAR(20) | NOT NULL | SEQUENTIAL/PARALLEL/AGREEMENT |
| status | VARCHAR(20) | NOT NULL | PENDING/APPROVED/REJECTED/HOLD/SKIPPED |
| comment | TEXT | NULL | 결재 의견 |
| acted_at | TIMESTAMP | NULL | 처리 일시 |
| acted_by | UUID | FK → users, NULL | 실제 처리자 (대결 시 대결자) |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |

### 4.3 approval_references (참조자)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| document_id | UUID | FK → approval_documents | 문서 ID |
| user_id | UUID | FK → users | 참조자 |
| is_read | BOOLEAN | DEFAULT false | 열람 여부 |
| read_at | TIMESTAMP | NULL | 열람 일시 |

### 4.4 approval_notifications (결재 알림)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| document_id | UUID | FK → approval_documents | 문서 ID |
| user_id | UUID | FK → users | 수신자 |
| type | VARCHAR(30) | NOT NULL | APPROVAL_REQUEST/APPROVED/REJECTED/REFERENCE |
| message | VARCHAR(500) | NOT NULL | 알림 메시지 |
| is_read | BOOLEAN | DEFAULT false | 읽음 여부 |
| is_email_sent | BOOLEAN | DEFAULT false | 이메일 발송 여부 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |

### 4.5 approval_saved_lines (저장된 결재선)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| name | VARCHAR(100) | NOT NULL | 결재선 이름 |
| user_id | UUID | FK → users | 소유자 |
| lines_json | JSONB | NOT NULL | 결재선 구성 정보 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |

### 4.6 관계도
- `approval_documents` 1:N `approval_lines` (한 문서에 여러 결재 단계)
- `approval_documents` 1:N `approval_references` (한 문서에 여러 참조자)
- `approval_documents` 1:N `approval_notifications` (한 문서에 여러 알림)
- `approval_documents` N:1 `document_templates` (양식 참조)
- `approval_lines` N:1 `users` (결재자)

## 5. API 명세

### 5.1 기안

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/approvals` | 결재 문서 생성 (임시저장) |
| PUT | `/api/v1/approvals/{id}` | 결재 문서 수정 |
| DELETE | `/api/v1/approvals/{id}` | 임시저장 문서 삭제 |
| GET | `/api/v1/approvals/{id}` | 결재 문서 상세 조회 |

**POST /api/v1/approvals**
```json
// Request
{
  "template_id": "uuid",
  "title": "2026년 3월 팀 회식비 품의",
  "content_json": {
    "purpose": "팀 분기 회식",
    "amount": 500000,
    "date": "2026-03-28"
  },
  "urgency": "NORMAL",
  "lines": [
    { "approver_id": "uuid", "step_order": 1, "line_type": "SEQUENTIAL" },
    { "approver_id": "uuid", "step_order": 2, "line_type": "SEQUENTIAL" }
  ],
  "references": ["uuid", "uuid"]
}

// Response (201)
{
  "id": "uuid",
  "document_number": "APR-2026-00032",
  "status": "DRAFT",
  "created_at": "2026-03-23T10:00:00+09:00"
}
```

### 5.2 상신/취소

| Method | Path | 설명 |
|--------|------|------|
| PUT | `/api/v1/approvals/{id}/submit` | 상신 |
| PUT | `/api/v1/approvals/{id}/cancel` | 상신 취소 |

### 5.3 결재 처리

| Method | Path | 설명 |
|--------|------|------|
| PUT | `/api/v1/approvals/{id}/approve` | 승인 |
| PUT | `/api/v1/approvals/{id}/reject` | 반려 |
| PUT | `/api/v1/approvals/{id}/hold` | 보류 |

**PUT /api/v1/approvals/{id}/approve**
```json
// Request
{
  "comment": "승인합니다."
}

// Response (200)
{
  "id": "uuid",
  "status": "IN_PROGRESS",
  "current_step": 2,
  "message": "승인 처리되었습니다."
}
```

**PUT /api/v1/approvals/{id}/reject**
```json
// Request
{
  "comment": "예산 초과로 반려합니다. 금액 조정 후 재상신 바랍니다."
}
```

### 5.4 조회

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/approvals` | 결재 문서 목록 (필터: status, type, date_from, date_to) |
| GET | `/api/v1/approvals/{id}/lines` | 결재선 현황 조회 |
| GET | `/api/v1/approvals/{id}/history` | 결재 처리 이력 조회 |

## 6. 화면 설계

### 6.1 기안 작성 페이지
```
┌─────────────────────────────────────────────┐
│ 결재 문서 작성                                │
├─────────────────────────────────────────────┤
│ 양식 선택: [품의서 ▼]                         │
│ 긴급도: ○ 일반  ○ 긴급  ○ 긴급(최우선)        │
│ 제목: [________________________]              │
├─────────────────────────────────────────────┤
│ ┌─ 문서 내용 ─────────────────────────────┐ │
│ │ (양식별 동적 폼 필드)                      │ │
│ │ 목적: [____________]                      │ │
│ │ 금액: [____________] 원                   │ │
│ │ 일자: [____-__-__]                        │ │
│ └──────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ ┌─ 결재선 설정 ───────────────────────────┐ │
│ │ [결재선 불러오기]  [조직도에서 선택]        │ │
│ │                                           │ │
│ │ 1단계(순차): 김팀장 (과장)    [×]          │ │
│ │ 2단계(순차): 이본부장 (부장)  [×]          │ │
│ │ [+ 결재자 추가]                            │ │
│ │                                           │ │
│ │ 참조: 박대리, 정사원           [+ 추가]    │ │
│ └──────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ 첨부파일: [파일 추가]                         │
├─────────────────────────────────────────────┤
│          [임시저장]  [상신]  [취소]            │
└─────────────────────────────────────────────┘
```

### 6.2 결재 처리 페이지
```
┌─────────────────────────────────────────────┐
│ 결재 문서 상세                                │
├─────────────────────────────────────────────┤
│ 문서번호: APR-2026-00032                      │
│ 양식: 품의서  |  긴급도: 일반                  │
│ 기안자: 홍길동 (개발팀/대리)                   │
│ 상신일: 2026-03-23 10:00                      │
├─────────────────────────────────────────────┤
│ ┌─ 결재선 현황 ───────────────────────────┐ │
│ │ ✅ 1단계: 김팀장 - 승인 (03-23 11:00)    │ │
│ │ ⏳ 2단계: 이본부장 - 대기중               │ │
│ └──────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ ┌─ 문서 내용 ─────────────────────────────┐ │
│ │ (양식 내용 표시)                           │ │
│ └──────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ 첨부파일: 견적서.pdf (2.1MB) [다운로드]       │
├─────────────────────────────────────────────┤
│ 의견: [________________________________]      │
│      [승인]  [반려]  [보류]                   │
└─────────────────────────────────────────────┘
```

## 7. 인수 조건

- [ ] 기안자가 양식을 선택하고 문서를 작성하여 임시저장할 수 있다
- [ ] 임시저장된 문서에 결재선을 설정하고 상신할 수 있다
- [ ] 상신된 문서는 첫 결재자에게 알림이 발송된다
- [ ] 결재자가 승인하면 다음 결재자에게 알림이 발송된다
- [ ] 모든 결재자가 승인하면 문서 상태가 APPROVED로 변경된다
- [ ] 결재자가 반려하면 기안자에게 반려 알림이 발송되고 문서 상태가 REJECTED로 변경된다
- [ ] 반려 시 사유 입력은 필수이다
- [ ] 첫 결재자 처리 전에만 상신 취소가 가능하다
- [ ] 병렬결재 시 해당 단계의 모든 결재자가 승인해야 다음 단계로 진행된다
- [ ] 합의 결재자는 의견만 제출하며 거부권이 없다
- [ ] 대결자가 지정된 경우 대결자가 결재를 처리할 수 있다
- [ ] 결재 이력은 수정/삭제가 불가능하다

## 8. 참고사항

- 전결/대결/후결은 MVP 이후 구현 가능 (초기에는 순차결재/병렬결재/합의만 구현)
- 결재 문서 내용은 JSONB로 저장하여 양식별 유연한 데이터 구조 지원
- 결재 알림은 비동기 처리 (Celery 또는 FastAPI BackgroundTasks 활용)
- 이메일 발송은 별도 이메일 서비스 연동 필요 (SMTP 또는 SES)
