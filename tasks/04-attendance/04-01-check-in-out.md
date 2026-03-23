# 04-01 출퇴근 관리

## 1. 개요

임직원의 일일 출퇴근 시간을 기록하고 근무시간을 자동 계산한다. 지각, 조퇴, 결근을 자동 판별하며, 유연근무제와 한국 공휴일 캘린더를 지원한다.

### 선행 의존성
- [01-01 인증](../01-auth-org/01-01-authentication.md) - 로그인 사용자 식별
- [01-03 조직도](../01-auth-org/01-03-org-chart.md) - 부서별 근무 스케줄

## 2. 기능 요구사항

### 2.1 출퇴근 기록
- [ ] 출근 버튼 클릭 시 현재 시각 기록
- [ ] 퇴근 버튼 클릭 시 현재 시각 기록
- [ ] 중복 출근/퇴근 방지 (당일 1회)
- [ ] 출퇴근 시각 수정 요청 기능 (관리자 승인 필요)
- [ ] 오늘의 출퇴근 상태 실시간 표시

### 2.2 근무시간 계산
- [ ] 기본 근무시간: 09:00~18:00 (점심 12:00~13:00, 실 근무 8시간)
- [ ] 근무시간 = 퇴근시각 - 출근시각 - 점심시간
- [ ] 주간 누적 근무시간 계산

### 2.3 유연근무제
- [ ] 시차출퇴근: 출근 가능 시간대 07:00~10:00
- [ ] 출근 시각 기준으로 퇴근 시각 자동 계산 (출근 후 9시간 = 8시간 근무 + 1시간 점심)
- [ ] 부서별/개인별 근무 스케줄 설정

### 2.4 근태 상태 자동 판별
- [ ] 정상 (NORMAL): 정시 출근 + 정시 이후 퇴근
- [ ] 지각 (LATE): 출근시간 이후 출근
- [ ] 조퇴 (EARLY_LEAVE): 퇴근시간 이전 퇴근
- [ ] 결근 (ABSENT): 출근 기록 없음 (휴일/휴가 제외)
- [ ] 휴가 (ON_LEAVE): 휴가 신청 승인됨

### 2.5 공휴일 관리
- [ ] 한국 법정 공휴일 등록 (매년 관리자가 등록)
  - 신정(1/1), 설날(음력 1/1 전후 3일), 삼일절(3/1), 어린이날(5/5)
  - 부처님오신날(음력 4/8), 현충일(6/6), 광복절(8/15)
  - 추석(음력 8/15 전후 3일), 개천절(10/3), 한글날(10/9), 성탄절(12/25)
- [ ] 대체공휴일 처리
- [ ] 회사 지정 휴일 (창립기념일 등)
- [ ] 연도별 공휴일 캘린더 관리

## 3. 비기능 요구사항

- 출퇴근 기록 응답 시간: 500ms 이내
- 출퇴근 기록은 수정/삭제 불가 (관리자 수정 요청 프로세스 별도)
- 타임존: Asia/Seoul 기준으로 날짜 판별
- 자정 기준 일자 변경 처리

## 4. 데이터베이스 스키마

### 4.1 attendance_records (출퇴근 기록)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| user_id | UUID | FK → users, NOT NULL | 사용자 |
| date | DATE | NOT NULL | 근무일 |
| check_in_at | TIMESTAMP | NULL | 출근 시각 |
| check_out_at | TIMESTAMP | NULL | 퇴근 시각 |
| work_minutes | INTEGER | NULL | 실 근무시간 (분) |
| status | VARCHAR(20) | NOT NULL | NORMAL/LATE/EARLY_LEAVE/ABSENT/ON_LEAVE |
| note | TEXT | NULL | 비고 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |

- UNIQUE 제약: (user_id, date)

### 4.2 work_schedules (근무 스케줄)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| name | VARCHAR(50) | NOT NULL | 스케줄명 (예: 기본근무, 유연근무) |
| start_time | TIME | NOT NULL | 출근 시각 (09:00) |
| end_time | TIME | NOT NULL | 퇴근 시각 (18:00) |
| lunch_start | TIME | NOT NULL | 점심 시작 (12:00) |
| lunch_end | TIME | NOT NULL | 점심 종료 (13:00) |
| is_flexible | BOOLEAN | DEFAULT false | 유연근무 여부 |
| flex_start_from | TIME | NULL | 유연출근 시작 (07:00) |
| flex_start_to | TIME | NULL | 유연출근 종료 (10:00) |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |

### 4.3 user_schedules (사용자별 스케줄 배정)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| user_id | UUID | FK → users | 사용자 |
| schedule_id | UUID | FK → work_schedules | 스케줄 |
| effective_from | DATE | NOT NULL | 적용 시작일 |
| effective_to | DATE | NULL | 적용 종료일 (NULL이면 현재 적용중) |

### 4.4 holidays (공휴일/휴일)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| date | DATE | NOT NULL | 휴일 날짜 |
| name | VARCHAR(50) | NOT NULL | 휴일명 |
| type | VARCHAR(20) | NOT NULL | PUBLIC(법정)/COMPANY(회사)/SUBSTITUTE(대체) |
| year | INTEGER | NOT NULL | 연도 |
| created_by | UUID | FK → users | 등록자 |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |

- UNIQUE 제약: (date)

## 5. API 명세

### 5.1 출퇴근

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/attendance/check-in` | 출근 기록 |
| POST | `/api/v1/attendance/check-out` | 퇴근 기록 |
| GET | `/api/v1/attendance/today` | 오늘 출퇴근 현황 |
| GET | `/api/v1/attendance/monthly` | 월간 출퇴근 내역 |

**POST /api/v1/attendance/check-in**
```json
// Request (body 없음, 인증 토큰으로 사용자 식별)

// Response (201)
{
  "id": "uuid",
  "date": "2026-03-23",
  "check_in_at": "2026-03-23T08:55:00+09:00",
  "status": "NORMAL",
  "message": "출근이 정상 기록되었습니다."
}
```

**GET /api/v1/attendance/monthly?year=2026&month=3**
```json
// Response (200)
{
  "year": 2026,
  "month": 3,
  "summary": {
    "work_days": 22,
    "attended_days": 18,
    "late_days": 1,
    "early_leave_days": 0,
    "absent_days": 0,
    "leave_days": 3,
    "total_work_hours": 144.5
  },
  "records": [
    {
      "date": "2026-03-02",
      "check_in_at": "2026-03-02T09:00:00+09:00",
      "check_out_at": "2026-03-02T18:05:00+09:00",
      "work_minutes": 480,
      "status": "NORMAL"
    }
  ]
}
```

### 5.2 공휴일

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/holidays` | 공휴일 목록 (쿼리: year) |
| POST | `/api/v1/holidays` | 공휴일 등록 (관리자) |
| PUT | `/api/v1/holidays/{id}` | 공휴일 수정 (관리자) |
| DELETE | `/api/v1/holidays/{id}` | 공휴일 삭제 (관리자) |

### 5.3 근무 스케줄

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/work-schedules` | 스케줄 목록 |
| POST | `/api/v1/work-schedules` | 스케줄 등록 (관리자) |
| PUT | `/api/v1/work-schedules/{id}` | 스케줄 수정 (관리자) |
| PUT | `/api/v1/users/{id}/schedule` | 사용자 스케줄 배정 (관리자) |

## 6. 화면 설계

### 6.1 출퇴근 위젯 (메인 대시보드)
```
┌────────────────────────────┐
│ 오늘의 근무                  │
│                             │
│ 2026년 3월 23일 (월)         │
│ 상태: ✅ 근무중               │
│                             │
│ 출근: 08:55                  │
│ 퇴근: --:--                  │
│ 근무시간: 5시간 30분 (진행중)  │
│                             │
│     [퇴근하기]               │
└────────────────────────────┘
```

### 6.2 월간 출퇴근 달력
```
┌──────────────────────────────────────────────┐
│ 2026년 3월 출퇴근 현황      [< 2월] [4월 >]    │
├──────┬──────┬──────┬──────┬──────┬──────┬────┤
│ 일   │ 월    │ 화    │ 수    │ 목    │ 금   │ 토 │
├──────┼──────┼──────┼──────┼──────┼──────┼────┤
│      │      │      │      │      │      │    │
│      │ 2    │ 3    │ 4    │ 5    │ 6    │ 7  │
│      │ ✅정상│ ✅정상│ ✅정상│ ⚠️지각│ ✅정상│    │
│      │ 8h   │ 8h   │ 8h   │ 7h30 │ 8h15 │    │
├──────┼──────┼──────┼──────┼──────┼──────┼────┤
│ 8    │ 9    │ ...  │      │      │      │    │
└──────┴──────┴──────┴──────┴──────┴──────┴────┘
│ 이번 달 요약: 출근 18일 | 지각 1회 | 연차 3일    │
└──────────────────────────────────────────────┘
```

## 7. 인수 조건

- [ ] 출근 버튼 클릭 시 현재 시각이 기록되고 상태가 표시된다
- [ ] 퇴근 버튼 클릭 시 현재 시각이 기록되고 근무시간이 계산된다
- [ ] 당일 중복 출근/퇴근이 방지된다
- [ ] 09:00 이후 출근 시 지각으로 자동 판별된다
- [ ] 유연근무 설정된 사용자는 설정된 시간 기준으로 판별된다
- [ ] 공휴일/주말에는 결근으로 처리되지 않는다
- [ ] 월간 달력 뷰에서 출퇴근 현황을 한눈에 확인할 수 있다
- [ ] 관리자가 공휴일을 등록/수정/삭제할 수 있다

## 8. 참고사항

- IP 기반 사내 네트워크 확인은 선택사항 (추후 보안 강화 시 적용)
- GPS 기반 위치 확인은 모바일 앱 개발 시 추가
- 출퇴근 기록 위변조 방지를 위해 서버 시각 기준으로 기록
- 일 변경 기준: 자정 (00:00 KST)
- 야간 근무자의 경우 날짜 변경 처리 로직 필요 (04-03 초과근무와 연동)
