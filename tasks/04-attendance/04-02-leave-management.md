# 04-02 휴가 관리

## 1. 개요

근로기준법에 따른 연차 자동 부여 및 휴가 신청/승인 프로세스를 관리한다. 연차, 반차, 특별휴가 등 다양한 휴가 유형을 지원하며, 잔여 연차 조회와 연차 촉진 알림 기능을 제공한다.

### 선행 의존성
- [01-03 조직도](../01-auth-org/01-03-org-chart.md) - 부서별 휴가 현황
- [02-01 결재 워크플로우](../02-approval/02-01-approval-workflow.md) - 휴가 신청 결재 연동 (선택)

## 2. 기능 요구사항

### 2.1 휴가 유형
- [ ] 연차 (ANNUAL): 유급 휴가, 근로기준법 기반 자동 부여
- [ ] 오전반차 (AM_HALF): 0.5일 차감, 오전 휴가 (오후 출근)
- [ ] 오후반차 (PM_HALF): 0.5일 차감, 오후 휴가 (오전 근무 후 퇴근)
- [ ] 특별휴가 (SPECIAL): 경조사 휴가
  - 본인 결혼: 5일
  - 자녀 결혼: 1일
  - 배우자 출산: 10일
  - 부모/배우자 사망: 5일
  - 조부모/형제자매 사망: 3일
- [ ] 공가 (OFFICIAL): 예비군, 민방위, 건강검진 등
- [ ] 병가 (SICK): 유급 병가 (연 60일 한도, 진단서 필요)

### 2.2 연차 자동 부여 (근로기준법)
- [ ] 입사 1년 미만: 1개월 개근 시 1일 발생 (최대 11일)
- [ ] 입사 1년 이상: 15일 부여
- [ ] 3년 이상 근속 시 매 2년마다 1일 가산 (최대 25일)
- [ ] 연차 발생 기준: 입사일 기준 (회계연도 기준 전환 가능)
- [ ] 연차 발생 이력 자동 기록

### 2.3 연차 촉진제도
- [ ] 잔여 연차 10일 이상 시 사용 촉진 1차 알림 (연차 발생일 6개월 전)
- [ ] 2차 알림 (연차 발생일 2개월 전)
- [ ] 촉진 알림 발송 기록 관리
- [ ] 미사용 연차 소멸 안내

### 2.4 휴가 신청/승인
- [ ] 휴가 신청: 유형 선택, 기간 선택, 사유 입력
- [ ] 승인 프로세스: 소속 팀장 승인 (또는 전자결재 연동)
- [ ] 신청 취소: 승인 전 취소 가능, 승인 후 취소 시 관리자 승인 필요
- [ ] 잔여 연차 초과 신청 방지

### 2.5 휴가 이월
- [ ] 미사용 연차: 다음 해 이월 불가 (소멸)
- [ ] 회계연도 기준 3개월 유예 가능 (설정)
- [ ] 연차 소멸 시 알림

## 3. 비기능 요구사항

- 연차 부여 배치: 매일 00:00 자동 실행 (입사 1년 미만 월별 부여)
- 연차 잔여 조회 응답 시간: 500ms 이내
- 근로기준법 준수 필수 (법적 분쟁 방지)
- 연차 발생/사용/소멸 이력 영구 보존

## 4. 데이터베이스 스키마

### 4.1 leave_types (휴가 유형)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| name | VARCHAR(50) | NOT NULL | 유형명 (연차, 오전반차, ...) |
| code | VARCHAR(20) | UNIQUE, NOT NULL | 코드 (ANNUAL, AM_HALF, ...) |
| is_paid | BOOLEAN | DEFAULT true | 유급 여부 |
| is_deductible | BOOLEAN | DEFAULT true | 연차 차감 여부 |
| deduction_days | DECIMAL(3,1) | DEFAULT 1.0 | 차감 일수 (반차: 0.5) |
| default_days | INTEGER | NULL | 기본 부여 일수 (특별휴가) |
| requires_document | BOOLEAN | DEFAULT false | 증빙 필요 여부 |
| description | TEXT | NULL | 설명 |
| is_active | BOOLEAN | DEFAULT true | 활성화 |
| sort_order | INTEGER | DEFAULT 0 | 정렬 |

### 4.2 leave_balances (연차 잔액)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| user_id | UUID | FK → users | 사용자 |
| leave_type_id | UUID | FK → leave_types | 휴가 유형 |
| year | INTEGER | NOT NULL | 연도 |
| total_days | DECIMAL(4,1) | NOT NULL | 총 부여 일수 |
| used_days | DECIMAL(4,1) | DEFAULT 0 | 사용 일수 |
| remaining_days | DECIMAL(4,1) | GENERATED | 잔여 일수 (total - used) |
| expires_at | DATE | NOT NULL | 소멸일 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |

- UNIQUE 제약: (user_id, leave_type_id, year)

### 4.3 leave_requests (휴가 신청)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| user_id | UUID | FK → users | 신청자 |
| leave_type_id | UUID | FK → leave_types | 휴가 유형 |
| start_date | DATE | NOT NULL | 시작일 |
| end_date | DATE | NOT NULL | 종료일 |
| days | DECIMAL(4,1) | NOT NULL | 사용 일수 |
| reason | TEXT | NULL | 사유 |
| status | VARCHAR(20) | NOT NULL | PENDING/APPROVED/REJECTED/CANCELLED |
| approver_id | UUID | FK → users, NULL | 승인자 |
| approved_at | TIMESTAMP | NULL | 승인 일시 |
| approval_comment | TEXT | NULL | 승인/반려 의견 |
| approval_document_id | UUID | FK → approval_documents, NULL | 결재 문서 ID (연동 시) |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |
| deleted_at | TIMESTAMP | NULL | 삭제 시각 |

### 4.4 leave_accrual_log (연차 발생 이력)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| user_id | UUID | FK → users | 사용자 |
| year | INTEGER | NOT NULL | 연도 |
| month | INTEGER | NULL | 월 (월별 발생 시) |
| accrued_days | DECIMAL(4,1) | NOT NULL | 발생 일수 |
| reason | VARCHAR(100) | NOT NULL | 발생 사유 (월별발생/연간부여/근속가산) |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |

## 5. API 명세

### 5.1 연차 잔액

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/leaves/balance` | 내 연차 잔액 조회 |
| GET | `/api/v1/leaves/balance/{userId}` | 특정 사용자 연차 잔액 (관리자) |

**GET /api/v1/leaves/balance**
```json
// Response (200)
{
  "year": 2026,
  "annual": {
    "total_days": 15,
    "used_days": 5.5,
    "remaining_days": 9.5,
    "expires_at": "2027-03-22"
  },
  "special": {
    "total_days": 0,
    "used_days": 0,
    "remaining_days": 0
  },
  "accrual_history": [
    { "date": "2025-03-23", "days": 15, "reason": "연간 부여 (입사 3년차)" }
  ]
}
```

### 5.2 휴가 신청

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/leaves/requests` | 휴가 신청 |
| GET | `/api/v1/leaves/requests` | 내 휴가 신청 목록 |
| GET | `/api/v1/leaves/requests/{id}` | 휴가 신청 상세 |
| PUT | `/api/v1/leaves/requests/{id}` | 휴가 신청 수정 (PENDING 상태) |
| DELETE | `/api/v1/leaves/requests/{id}` | 휴가 신청 취소 |

**POST /api/v1/leaves/requests**
```json
// Request
{
  "leave_type_id": "uuid",
  "start_date": "2026-04-01",
  "end_date": "2026-04-03",
  "days": 3,
  "reason": "가족 여행"
}

// Response (201)
{
  "id": "uuid",
  "status": "PENDING",
  "message": "휴가 신청이 접수되었습니다. 승인 대기 중입니다."
}
```

### 5.3 휴가 승인 (팀장/관리자)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/leaves/requests/pending` | 승인 대기 목록 (팀장) |
| POST | `/api/v1/leaves/requests/{id}/approve` | 승인 |
| POST | `/api/v1/leaves/requests/{id}/reject` | 반려 |

### 5.4 팀 휴가 현황

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/leaves/team-calendar` | 팀 휴가 캘린더 (쿼리: year, month) |

```json
// Response (200)
{
  "year": 2026,
  "month": 4,
  "members": [
    {
      "user_id": "uuid",
      "name": "홍길동",
      "leaves": [
        { "start_date": "2026-04-01", "end_date": "2026-04-03", "type": "연차", "status": "APPROVED" }
      ]
    }
  ]
}
```

## 6. 화면 설계

### 6.1 휴가 신청 폼
```
┌──────────────────────────────────────────┐
│ 휴가 신청                                 │
├──────────────────────────────────────────┤
│ 잔여 연차: 9.5일 / 15일                   │
├──────────────────────────────────────────┤
│ 휴가 유형: [연차 ▼]                       │
│                                          │
│ 기간: [2026-04-01] ~ [2026-04-03]        │
│ 사용 일수: 3일                            │
│                                          │
│ 사유: [가족 여행_______________]           │
│                                          │
│ 승인자: 김팀장 (자동 지정)                 │
├──────────────────────────────────────────┤
│           [신청]  [취소]                  │
└──────────────────────────────────────────┘
```

### 6.2 내 휴가 현황
```
┌──────────────────────────────────────────┐
│ 내 휴가 현황  2026년                      │
├──────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ 총 연차   │ │ 사용      │ │ 잔여     │ │
│ │  15일    │ │  5.5일   │ │  9.5일   │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│ ████████████████░░░░░░░░░ 36.7% 사용    │
├──────────────────────────────────────────┤
│ 사용 내역                                 │
├────┬──────┬──────────┬──────────┬───────┤
│ #  │ 유형  │ 기간      │ 일수     │ 상태  │
├────┼──────┼──────────┼──────────┼───────┤
│ 1  │ 연차  │ 04-01~03 │ 3.0일   │ 대기  │
│ 2  │ 반차  │ 03-15    │ 0.5일   │ 승인  │
│ 3  │ 연차  │ 02-10~11 │ 2.0일   │ 승인  │
│ 4  │ 연차  │ 01-20~22 │ 3.0일   │ 승인  │
└────┴──────┴──────────┴──────────┴───────┘
```

### 6.3 팀 휴가 캘린더
```
┌──────────────────────────────────────────┐
│ 팀 휴가 캘린더  2026년 4월                 │
├────────┬──┬──┬──┬──┬──┬──┬──┬──┬──┬─────┤
│ 이름    │1 │2 │3 │4 │5 │6 │7 │8 │9 │... │
├────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼─────┤
│ 홍길동  │██│██│██│  │  │  │  │  │  │     │
│ 김개발  │  │  │  │  │  │  │██│██│  │     │
│ 박디자인│  │  │  │  │  │  │  │  │  │     │
└────────┴──┴──┴──┴──┴──┴──┴──┴──┴──┴─────┘
│ ██ 연차  ▓▓ 반차  ░░ 특별휴가              │
└──────────────────────────────────────────┘
```

## 7. 인수 조건

- [ ] 입사 1년 미만 직원에게 매월 1일의 연차가 자동 부여된다
- [ ] 입사 1년 이상 직원에게 15일의 연차가 자동 부여된다
- [ ] 3년 이상 근속 시 매 2년마다 1일이 가산된다 (최대 25일)
- [ ] 잔여 연차를 초과하여 신청할 수 없다
- [ ] 반차 신청 시 0.5일이 차감된다
- [ ] 휴가 신청이 승인되면 출퇴근 기록에 ON_LEAVE로 반영된다
- [ ] 팀장이 소속 팀원의 휴가 신청을 승인/반려할 수 있다
- [ ] 팀 휴가 캘린더에서 팀원의 휴가 일정을 확인할 수 있다
- [ ] 연차 소멸 전 촉진 알림이 발송된다

## 8. 참고사항

- 연차 부여 기준(입사일/회계연도)은 시스템 설정으로 전환 가능하도록 설계
- 특별휴가(경조사)는 증빙 서류 제출 필요 (첨부파일 연동)
- 전자결재 연동 시 휴가신청서 양식으로 결재 진행 가능
- 연차 계산 로직은 단위 테스트 필수 (근로기준법 기준 검증)
- 연차 부여 배치 작업은 Celery Beat 또는 APScheduler 활용
