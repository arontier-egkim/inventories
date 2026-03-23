# 04-04 근태 현황 및 리포트

## 1. 개요

개인/부서/전사 단위의 근태 현황을 조회하고 리포트를 생성한다. 출근율, 지각율, 연차 소진율, 주 52시간 초과 현황 등을 시각화하며, 엑셀 다운로드 기능을 제공한다.

### 선행 의존성
- [04-01 출퇴근 관리](04-01-check-in-out.md) - 출퇴근 기록 데이터
- [04-02 휴가 관리](04-02-leave-management.md) - 휴가 사용 데이터
- [04-03 초과근무 관리](04-03-overtime.md) - 초과근무 데이터

## 2. 기능 요구사항

### 2.1 개인 근태 현황
- [ ] 월간 출근일수, 지각 횟수, 조퇴 횟수, 결근 횟수
- [ ] 연차 사용 현황 (사용/잔여 비율)
- [ ] 초과근무 시간 합계
- [ ] 총 근무시간
- [ ] 월별 추이 그래프

### 2.2 부서별 근태 통계 (부서관리자 이상)
- [ ] 부서원 출근율 (출근일/근무일)
- [ ] 부서 평균 근무시간
- [ ] 지각율
- [ ] 연차 소진율 (사용/부여)
- [ ] 부서원별 근태 요약 테이블

### 2.3 관리자 리포트 (시스템관리자/인사)
- [ ] 전사 근태 현황 요약
- [ ] 주 52시간 초과 현황 (초과자 목록)
- [ ] 연차 미사용 현황 (연차 촉진 대상자 목록)
- [ ] 부서별 비교 통계

### 2.4 엑셀 다운로드
- [ ] 월간 근태 상세 데이터 (개인별 일자별 출퇴근 시각, 근무시간, 상태)
- [ ] 부서별 근태 요약
- [ ] 연차 사용 현황

### 2.5 대시보드 위젯
- [ ] 메인 페이지에 개인 근태 요약 위젯 표시
- [ ] 이번 달 출근일수, 잔여 연차, 주간 근무시간

## 3. 비기능 요구사항

- 리포트 조회 응답 시간: 3초 이내 (대규모 데이터 집계)
- 엑셀 생성: 비동기 처리 (대용량 시 다운로드 링크 제공)
- 리포트 데이터 캐싱: 당월 데이터는 1시간 캐시

## 4. 데이터베이스 스키마

이 태스크는 새로운 테이블을 생성하지 않으며, 기존 테이블을 집계 조회한다.

### 4.1 주요 집계 뷰/인덱스

| 대상 테이블 | 인덱스/뷰 | 용도 |
|------------|----------|------|
| `attendance_records` | `idx_attendance_user_date` (user_id, date) | 개인 월간 조회 |
| `attendance_records` | `idx_attendance_status_date` (status, date) | 상태별 집계 |
| `leave_balances` | `idx_balance_user_year` (user_id, year) | 연차 현황 |
| `weekly_work_summary` | `idx_weekly_exceeded` (is_exceeded, year, week_number) | 52시간 초과 조회 |

### 4.2 집계 쿼리 예시 (월간 개인 근태)

```sql
SELECT
  u.name,
  COUNT(CASE WHEN ar.status = 'NORMAL' THEN 1 END) AS normal_days,
  COUNT(CASE WHEN ar.status = 'LATE' THEN 1 END) AS late_days,
  COUNT(CASE WHEN ar.status = 'EARLY_LEAVE' THEN 1 END) AS early_leave_days,
  COUNT(CASE WHEN ar.status = 'ABSENT' THEN 1 END) AS absent_days,
  COUNT(CASE WHEN ar.status = 'ON_LEAVE' THEN 1 END) AS leave_days,
  SUM(ar.work_minutes) / 60.0 AS total_work_hours
FROM attendance_records ar
JOIN users u ON u.id = ar.user_id
WHERE ar.user_id = :user_id
  AND ar.date BETWEEN :start_date AND :end_date
GROUP BY u.name;
```

## 5. API 명세

### 5.1 개인 리포트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/attendance/report/personal` | 개인 근태 리포트 |

**GET /api/v1/attendance/report/personal?year=2026&month=3**
```json
// Response (200)
{
  "year": 2026,
  "month": 3,
  "work_days_in_month": 22,
  "summary": {
    "attended_days": 18,
    "normal_days": 17,
    "late_days": 1,
    "early_leave_days": 0,
    "absent_days": 0,
    "leave_days": 3,
    "overtime_hours": 12.5,
    "total_work_hours": 156.5,
    "attendance_rate": 95.5
  },
  "annual_leave": {
    "total": 15,
    "used": 5.5,
    "remaining": 9.5
  }
}
```

### 5.2 부서 리포트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/attendance/report/department` | 부서 근태 리포트 |

**GET /api/v1/attendance/report/department?department_id=uuid&year=2026&month=3**
```json
// Response (200)
{
  "department": { "id": "uuid", "name": "개발팀" },
  "member_count": 8,
  "summary": {
    "avg_attendance_rate": 96.2,
    "avg_work_hours": 165.3,
    "late_rate": 3.5,
    "leave_usage_rate": 42.0
  },
  "members": [
    {
      "user_id": "uuid",
      "name": "홍길동",
      "attended_days": 20,
      "late_days": 0,
      "leave_days": 2,
      "overtime_hours": 8,
      "total_work_hours": 168
    }
  ]
}
```

### 5.3 전사 리포트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/attendance/report/company` | 전사 근태 리포트 (관리자) |

### 5.4 엑셀 내보내기

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/attendance/report/export` | 엑셀 다운로드 |

**GET /api/v1/attendance/report/export?format=xlsx&year=2026&month=3&type=personal**

Response: `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

## 6. 화면 설계

### 6.1 개인 근태 대시보드
```
┌──────────────────────────────────────────────────┐
│ 내 근태 현황  2026년 3월          [엑셀 다운로드]   │
├──────────────────────────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │출근   │ │지각   │ │조퇴   │ │연차   │ │초과근무│   │
│ │ 18일 │ │ 1회  │ │ 0회  │ │ 3일  │ │12.5h │   │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
├──────────────────────────────────────────────────┤
│ 총 근무시간: 156.5시간  |  출근율: 95.5%           │
│ 연차: 5.5 / 15일 사용 (잔여 9.5일)                │
│ ████████████░░░░░░░░░░ 36.7%                     │
├──────────────────────────────────────────────────┤
│ ┌─ 월별 근무시간 추이 ─────────────────────────┐ │
│ │    ██                                        │ │
│ │ ██ ██ ██                                     │ │
│ │ 1월 2월 3월                                   │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### 6.2 부서 근태 현황 (관리자)
```
┌──────────────────────────────────────────────────┐
│ 부서 근태 현황  개발팀  2026년 3월                   │
├──────────────────────────────────────────────────┤
│ 평균 출근율: 96.2%  |  평균 근무시간: 165.3h        │
│ 지각율: 3.5%  |  연차 소진율: 42.0%                 │
├────┬──────┬──────┬──────┬──────┬───────┬────────┤
│ #  │ 이름  │ 출근  │ 지각  │ 연차  │ 초과근무 │ 총근무  │
├────┼──────┼──────┼──────┼──────┼───────┼────────┤
│ 1  │ 홍길동│ 20일 │ 0회  │ 2일  │ 8h    │ 168h   │
│ 2  │ 김개발│ 19일 │ 1회  │ 3일  │ 15h   │ 167h   │
│ 3  │ 박디자│ 21일 │ 0회  │ 1일  │ 4h    │ 172h   │
│ ...│      │      │      │      │       │        │
└────┴──────┴──────┴──────┴──────┴───────┴────────┘
```

### 6.3 52시간 초과 경고 (관리자)
```
┌──────────────────────────────────────────────────┐
│ ⚠️ 주 52시간 초과 현황                              │
├────┬──────┬──────┬───────┬────────┬─────────────┤
│ #  │ 이름  │ 부서  │ 주차   │ 총근무   │ 초과 시간    │
├────┼──────┼──────┼───────┼────────┼─────────────┤
│ 1  │ 김개발│ 개발팀│ 11주차 │ 55h    │ +3h         │
│ 2  │ 이영업│ 영업팀│ 11주차 │ 53h    │ +1h         │
└────┴──────┴──────┴───────┴────────┴─────────────┘
```

## 7. 인수 조건

- [ ] 개인 월간 근태 현황 (출근일수, 지각, 연차 등)을 조회할 수 있다
- [ ] 부서관리자가 소속 부서의 근태 통계를 조회할 수 있다
- [ ] 관리자가 전사 근태 현황 및 52시간 초과자를 조회할 수 있다
- [ ] 월간 근태 데이터를 엑셀로 다운로드할 수 있다
- [ ] 메인 대시보드에 개인 근태 요약 위젯이 표시된다
- [ ] 월별 근무시간 추이 차트가 정상 렌더링된다

## 8. 참고사항

- 리포트 데이터 집계는 materialized view 또는 Redis 캐시 활용 검토
- 엑셀 생성은 openpyxl (Python) 라이브러리 사용
- 대용량 데이터 (전사 1년치) 엑셀 생성 시 비동기 처리 + 다운로드 링크 제공
- 차트 라이브러리: shadcn/ui Charts 컴포넌트 사용 (Recharts 기반 래퍼)
