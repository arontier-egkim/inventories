# 02-02 문서 양식 관리

## 1. 개요

전자결재에서 사용하는 문서 양식을 관리한다. 관리자가 양식을 등록/수정하고, 기안자는 양식을 선택하여 문서를 작성한다. 양식은 JSON Schema 기반의 동적 폼 필드로 정의되어 다양한 문서 형태를 지원한다.

### 선행 의존성
- [02-01 결재 워크플로우](02-01-approval-workflow.md) - 양식이 결재 문서에서 사용됨

## 2. 기능 요구사항

### 2.1 기본 제공 양식
- [ ] 품의서: 일반 업무 품의 (목적, 내용, 금액, 기대효과)
- [ ] 지출결의서: 비용 지출 (지출항목, 금액, 증빙 첨부)
- [ ] 휴가신청서: 연차/반차/특별휴가 (휴가유형, 기간, 사유)
- [ ] 출장신청서: 출장 일정/비용 (출장지, 기간, 목적, 예상비용)
- [ ] 업무보고서: 주간/월간 보고 (보고기간, 수행업무, 계획)

### 2.2 양식 관리
- [ ] 양식 등록 (관리자)
- [ ] 양식 수정 (관리자)
- [ ] 양식 삭제 (사용 중인 양식은 비활성화만 가능)
- [ ] 양식 활성화/비활성화
- [ ] 양식 분류 (카테고리: 일반, 인사, 재무, 보고)
- [ ] 양식 정렬 순서 설정

### 2.3 동적 폼 필드
- [ ] 필드 타입: text, textarea, number, date, daterange, select, checkbox, radio, file, table
- [ ] 필드 속성: label, name, required, placeholder, default_value, validation
- [ ] 필드 유효성 검증: 필수값, 최소/최대 길이, 숫자 범위, 정규식
- [ ] 테이블 필드: 동적 행 추가/삭제 가능한 표 형태

### 2.4 기본 결재선
- [ ] 양식별 기본 결재선 템플릿 설정
- [ ] 결재자 지정 방식: 직접 지정, 직책 기반 (예: 소속 팀장 → 본부장), 부서장 자동 지정

## 3. 비기능 요구사항

- 양식 필드 스키마는 JSON Schema Draft 7 호환
- 양식 미리보기 시 실제 폼과 동일한 렌더링
- 양식 변경 시 기존 작성된 문서에는 영향 없음 (문서 생성 시 스키마 스냅샷 저장)

## 4. 데이터베이스 스키마

### 4.1 document_templates (문서 양식)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 양식 ID |
| name | VARCHAR(100) | NOT NULL | 양식명 |
| description | TEXT | NULL | 양식 설명 |
| category | VARCHAR(20) | NOT NULL | GENERAL/HR/FINANCE/REPORT |
| fields_schema_json | JSONB | NOT NULL | 폼 필드 정의 (JSON Schema) |
| is_active | BOOLEAN | DEFAULT true | 활성화 여부 |
| sort_order | INTEGER | DEFAULT 0 | 정렬 순서 |
| created_by | UUID | FK → users | 생성자 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_by | UUID | FK → users | 수정자 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |
| deleted_at | TIMESTAMP | NULL | 삭제 시각 |

### 4.2 template_default_lines (양식 기본 결재선)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| template_id | UUID | FK → document_templates | 양식 ID |
| step_order | INTEGER | NOT NULL | 결재 순서 |
| line_type | VARCHAR(20) | NOT NULL | SEQUENTIAL/PARALLEL/AGREEMENT |
| approver_type | VARCHAR(20) | NOT NULL | SPECIFIC_USER/POSITION/DEPT_HEAD |
| approver_value | VARCHAR(100) | NOT NULL | 사용자 ID 또는 직책 코드 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |

### 4.3 fields_schema_json 예시

```json
{
  "fields": [
    {
      "name": "purpose",
      "type": "textarea",
      "label": "품의 목적",
      "required": true,
      "placeholder": "품의 목적을 입력하세요"
    },
    {
      "name": "amount",
      "type": "number",
      "label": "금액 (원)",
      "required": true,
      "validation": { "min": 0 }
    },
    {
      "name": "expected_date",
      "type": "date",
      "label": "예정일",
      "required": true
    },
    {
      "name": "expense_items",
      "type": "table",
      "label": "지출 항목",
      "columns": [
        { "name": "item", "label": "항목", "type": "text" },
        { "name": "quantity", "label": "수량", "type": "number" },
        { "name": "unit_price", "label": "단가", "type": "number" },
        { "name": "total", "label": "합계", "type": "number", "computed": "quantity * unit_price" }
      ]
    }
  ]
}
```

## 5. API 명세

### 5.1 양식 CRUD

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/templates` | 양식 목록 조회 (필터: category, is_active) |
| GET | `/api/v1/templates/{id}` | 양식 상세 조회 |
| POST | `/api/v1/templates` | 양식 등록 (관리자) |
| PUT | `/api/v1/templates/{id}` | 양식 수정 (관리자) |
| DELETE | `/api/v1/templates/{id}` | 양식 삭제 (관리자) |
| GET | `/api/v1/templates/{id}/preview` | 양식 미리보기 (렌더링용 스키마 반환) |

**POST /api/v1/templates**
```json
// Request
{
  "name": "품의서",
  "description": "일반 업무 품의에 사용하는 양식입니다.",
  "category": "GENERAL",
  "fields_schema_json": { "fields": [...] },
  "default_lines": [
    { "step_order": 1, "line_type": "SEQUENTIAL", "approver_type": "DEPT_HEAD", "approver_value": "TEAM_LEADER" },
    { "step_order": 2, "line_type": "SEQUENTIAL", "approver_type": "DEPT_HEAD", "approver_value": "DIVISION_HEAD" }
  ]
}

// Response (201)
{
  "id": "uuid",
  "name": "품의서",
  "created_at": "2026-03-23T10:00:00+09:00"
}
```

## 6. 화면 설계

### 6.1 양식 목록 관리 (관리자)
```
┌──────────────────────────────────────────────┐
│ 문서 양식 관리                    [+ 양식 등록] │
├──────────────────────────────────────────────┤
│ 카테고리: [전체 ▼]  상태: [전체 ▼]             │
├────┬──────────┬──────┬──────┬──────┬────────┤
│ #  │ 양식명    │ 카테고리 │ 상태  │ 수정일 │ 관리   │
├────┼──────────┼──────┼──────┼──────┼────────┤
│ 1  │ 품의서    │ 일반   │ ✅활성 │ 03-20 │ [수정] │
│ 2  │ 지출결의서 │ 재무   │ ✅활성 │ 03-18 │ [수정] │
│ 3  │ 휴가신청서 │ 인사   │ ✅활성 │ 03-15 │ [수정] │
│ 4  │ 출장신청서 │ 일반   │ ⬜비활성│ 03-10 │ [수정] │
└────┴──────────┴──────┴──────┴──────┴────────┘
```

### 6.2 양식 편집기
```
┌──────────────────────────────────────────────┐
│ 양식 편집: 품의서                              │
├──────────────────────────────────────────────┤
│ 양식명: [품의서____________]                   │
│ 카테고리: [일반 ▼]                             │
│ 설명: [일반 업무 품의에 사용_____]              │
├──────────────────────────────────────────────┤
│ ┌─ 폼 필드 구성 ────────────────────────────┐│
│ │ ☰ 품의 목적  [textarea] 필수 ✅    [×]    ││
│ │ ☰ 금액       [number]   필수 ✅    [×]    ││
│ │ ☰ 예정일     [date]     필수 ✅    [×]    ││
│ │ ☰ 지출항목   [table]    필수 ⬜    [×]    ││
│ │                                           ││
│ │ [+ 필드 추가]                              ││
│ └───────────────────────────────────────────┘│
├──────────────────────────────────────────────┤
│ ┌─ 기본 결재선 ─────────────────────────────┐│
│ │ 1단계: [소속 팀장 ▼] (순차)                ││
│ │ 2단계: [본부장 ▼]    (순차)                ││
│ │ [+ 단계 추가]                              ││
│ └───────────────────────────────────────────┘│
├──────────────────────────────────────────────┤
│ [미리보기]  [저장]  [취소]                     │
└──────────────────────────────────────────────┘
```

## 7. 인수 조건

- [ ] 관리자가 새 양식을 등록할 수 있다
- [ ] 양식에 다양한 필드 타입(text, number, date, select, table 등)을 추가할 수 있다
- [ ] 양식 미리보기에서 실제 폼과 동일한 형태로 렌더링된다
- [ ] 기본 결재선을 설정하면 기안 시 자동으로 결재선이 채워진다
- [ ] 사용 중인 양식은 삭제할 수 없고 비활성화만 가능하다
- [ ] 양식을 수정해도 이미 작성된 문서에는 영향이 없다
- [ ] 기본 제공 양식 5종이 시스템 초기화 시 등록된다

## 8. 참고사항

- 양식 필드 스키마 변경 시 backward compatibility를 위해 버전 관리 고려
- table 타입 필드의 계산식(computed) 지원은 프론트엔드에서 처리
- 양식 미리보기는 Next.js 동적 폼 렌더링 컴포넌트로 구현
- 기본 결재선의 DEPT_HEAD 타입은 기안자의 소속 부서 기준으로 자동 매핑
