# 04-03 초과근무 관리

## 1. 개요

연장근무, 야간근무, 휴일근무 등 초과근무를 신청하고 관리한다. 근로기준법에 따라 주 52시간 준수 여부를 모니터링하고, 초과 시 경고 알림을 발송한다.

### 선행 의존성
- [04-01 출퇴근 관리](04-01-check-in-out.md) - 실 근무시간 데이터

## 2. 기능 요구사항

### 2.1 초과근무 유형
- [ ] 연장근무 (OVERTIME): 정규 근무시간(18:00) 이후 근무
- [ ] 야간근무 (NIGHT): 22:00~06:00 근무
- [ ] 휴일근무 (HOLIDAY): 공휴일 또는 주말 근무

### 2.2 초과근무 신청
- [ ] 사전 신청 원칙 (당일 또는 사전 신청)
- [ ] 신청 정보: 날짜, 유형, 예정 시작/종료 시각, 사유
- [ ] 팀장 승인 필요
- [ ] 실제 근무 시간은 출퇴근 기록에서 자동 반영

### 2.3 주 52시간 모니터링
- [ ] 주 단위 근무시간 자동 집계 (기본 40시간 + 초과근무)
- [ ] 48시간 초과 시 본인+관리자에게 경고 알림
- [ ] 52시간 초과 시 긴급 알림 (관리자/인사팀)
- [ ] 주간 근무시간 현황 대시보드

### 2.4 수당 계산 기준 (참고)
- [ ] 연장근무: 통상임금 × 1.5배
- [ ] 야간근무: 통상임금 × 0.5배 추가 (연장+야간 중복 시 2.0배)
- [ ] 휴일근무 8시간 이내: 통상임금 × 1.5배
- [ ] 휴일근무 8시간 초과: 통상임금 × 2.0배

## 3. 비기능 요구사항

- 주간 근무시간 집계: 매주 월요일 00:00 자동 배치
- 52시간 경고 알림: 실시간 (출퇴근 기록 시 계산)
- 초과근무 기록 영구 보존

## 4. 데이터베이스 스키마

### 4.1 overtime_requests (초과근무 신청)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| user_id | UUID | FK → users | 신청자 |
| date | DATE | NOT NULL | 근무일 |
| type | VARCHAR(20) | NOT NULL | OVERTIME/NIGHT/HOLIDAY |
| planned_start | TIME | NOT NULL | 예정 시작 시각 |
| planned_end | TIME | NOT NULL | 예정 종료 시각 |
| planned_hours | DECIMAL(4,1) | NOT NULL | 예정 시간 |
| actual_start | TIME | NULL | 실제 시작 시각 |
| actual_end | TIME | NULL | 실제 종료 시각 |
| actual_hours | DECIMAL(4,1) | NULL | 실제 시간 |
| reason | TEXT | NOT NULL | 사유 |
| status | VARCHAR(20) | NOT NULL | PENDING/APPROVED/REJECTED/COMPLETED |
| approver_id | UUID | FK → users | 승인자 |
| approved_at | TIMESTAMP | NULL | 승인 일시 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |
| deleted_at | TIMESTAMP | NULL | 삭제 시각 |

### 4.2 overtime_policies (초과근무 정책)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| name | VARCHAR(50) | NOT NULL | 정책명 |
| max_weekly_hours | INTEGER | DEFAULT 52 | 최대 주간 근무시간 |
| warning_threshold_hours | INTEGER | DEFAULT 48 | 경고 기준 시간 |
| max_overtime_per_week | INTEGER | DEFAULT 12 | 최대 주간 초과근무 |
| is_active | BOOLEAN | DEFAULT true | 활성화 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |

### 4.3 weekly_work_summary (주간 근무 요약)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| user_id | UUID | FK → users | 사용자 |
| year | INTEGER | NOT NULL | 연도 |
| week_number | INTEGER | NOT NULL | 주차 (ISO 8601) |
| week_start_date | DATE | NOT NULL | 주 시작일 (월요일) |
| regular_hours | DECIMAL(5,1) | DEFAULT 0 | 정규 근무시간 |
| overtime_hours | DECIMAL(5,1) | DEFAULT 0 | 초과근무시간 |
| total_hours | DECIMAL(5,1) | DEFAULT 0 | 총 근무시간 |
| is_warning | BOOLEAN | DEFAULT false | 경고 상태 (48시간 초과) |
| is_exceeded | BOOLEAN | DEFAULT false | 초과 상태 (52시간 초과) |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |

- UNIQUE 제약: (user_id, year, week_number)

## 5. API 명세

### 5.1 초과근무 신청

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/overtime/requests` | 초과근무 신청 |
| GET | `/api/v1/overtime/requests` | 내 초과근무 목록 |
| GET | `/api/v1/overtime/requests/{id}` | 초과근무 상세 |
| PUT | `/api/v1/overtime/requests/{id}` | 초과근무 수정 (PENDING) |
| DELETE | `/api/v1/overtime/requests/{id}` | 초과근무 취소 |

**POST /api/v1/overtime/requests**
```json
// Request
{
  "date": "2026-03-23",
  "type": "OVERTIME",
  "planned_start": "18:00",
  "planned_end": "21:00",
  "planned_hours": 3,
  "reason": "프로젝트 마감 대응"
}

// Response (201)
{
  "id": "uuid",
  "status": "PENDING",
  "weekly_total_after": 43,
  "message": "초과근무 신청이 접수되었습니다."
}
```

### 5.2 승인

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/overtime/requests/pending` | 승인 대기 목록 (팀장) |
| POST | `/api/v1/overtime/requests/{id}/approve` | 승인 |
| POST | `/api/v1/overtime/requests/{id}/reject` | 반려 |

### 5.3 주간 현황

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/overtime/weekly-summary` | 내 주간 근무시간 |
| GET | `/api/v1/overtime/weekly-summary/team` | 팀 주간 현황 (팀장) |
| GET | `/api/v1/overtime/alerts` | 52시간 초과 경고 목록 (관리자) |

**GET /api/v1/overtime/weekly-summary?year=2026&week=12**
```json
// Response (200)
{
  "year": 2026,
  "week_number": 12,
  "week_start_date": "2026-03-16",
  "regular_hours": 40,
  "overtime_hours": 6,
  "total_hours": 46,
  "max_weekly_hours": 52,
  "remaining_overtime": 6,
  "is_warning": false,
  "daily_breakdown": [
    { "date": "2026-03-16", "regular": 8, "overtime": 2, "type": "OVERTIME" },
    { "date": "2026-03-17", "regular": 8, "overtime": 0, "type": null },
    { "date": "2026-03-18", "regular": 8, "overtime": 1, "type": "OVERTIME" },
    { "date": "2026-03-19", "regular": 8, "overtime": 3, "type": "OVERTIME" },
    { "date": "2026-03-20", "regular": 8, "overtime": 0, "type": null }
  ]
}
```

## 6. 화면 설계

### 6.1 초과근무 신청 폼
```
┌──────────────────────────────────────────┐
│ 초과근무 신청                              │
├──────────────────────────────────────────┤
│ 이번 주 현황: 40h 정규 + 3h 초과 = 43h    │
│ ████████████████████░░░░░ 43/52시간       │
│ 잔여 초과근무 가능: 9시간                   │
├──────────────────────────────────────────┤
│ 날짜: [2026-03-23]                        │
│ 유형: ○ 연장근무  ○ 야간근무  ○ 휴일근무    │
│ 시간: [18:00] ~ [21:00] (3시간)           │
│ 사유: [프로젝트 마감 대응__________]        │
├──────────────────────────────────────────┤
│           [신청]  [취소]                   │
└──────────────────────────────────────────┘
```

### 6.2 주간 근무시간 현황
```
┌──────────────────────────────────────────┐
│ 주간 근무시간  2026년 12주차 (3/16~3/20)   │
├──────────────────────────────────────────┤
│ ┌────────────────────────────────────┐   │
│ │ 정규: 40h  초과: 6h  합계: 46h     │   │
│ │ ████████████████████████░░░░ 46/52 │   │
│ └────────────────────────────────────┘   │
├──────┬──────┬──────┬──────┬──────┬──────┤
│      │ 월   │ 화    │ 수   │ 목   │ 금   │
│ 정규  │ 8h  │ 8h   │ 8h   │ 8h   │ 8h   │
│ 초과  │ 2h  │ 0h   │ 1h   │ 3h   │ 0h   │
│ 합계  │ 10h │ 8h   │ 9h   │ 11h  │ 8h   │
└──────┴──────┴──────┴──────┴──────┴──────┘
```

## 7. 인수 조건

- [ ] 초과근무를 신청하고 팀장의 승인을 받을 수 있다
- [ ] 승인된 초과근무의 실제 시간이 출퇴근 기록에서 자동 반영된다
- [ ] 주간 근무시간이 48시간 초과 시 경고 알림이 발송된다
- [ ] 주간 근무시간이 52시간 초과 시 긴급 알림이 관리자에게 발송된다
- [ ] 52시간 초과 상태에서 추가 초과근무 신청 시 경고 메시지가 표시된다
- [ ] 주간 근무시간 현황을 프로그레스 바로 확인할 수 있다
- [ ] 일별 근무시간 내역을 확인할 수 있다

## 8. 참고사항

- 수당 계산은 참고용 표시만 제공 (실제 급여 연동은 별도 시스템)
- 주 52시간 계산 기준: 월요일~일요일 (ISO 8601)
- 포괄임금제 적용 여부에 따라 수당 계산 방식 다를 수 있음 (설정 가능)
- 5인 미만 사업장은 주 52시간 적용 제외 (설정으로 비활성화 가능)
