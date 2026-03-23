# 05-03 자산 현황 및 리포트

## 1. 개요

등록된 자산 데이터를 기반으로 다양한 관점의 현황 대시보드와 리포트를 제공한다. 전체 자산 현황, 카테고리별/부서별 분석, 보증 만료 알림, 감가상각 참고 정보 등을 시각화하며, 엑셀 내보내기를 통해 오프라인 보고서 작성을 지원한다.

- **모듈**: 자산관리 (Inventories)
- **의존성**: `05-01` 자산 등록 및 분류, `05-02` 자산 배정 및 반납
- **기술 스택**: Next.js (프론트엔드) + FastAPI (백엔드) + PostgreSQL (데이터베이스)

---

## 2. 기능 요구사항

### 2.1 전체 자산 현황 대시보드

- **요약 카드**: 총 자산 수, 상태별 자산 수 (사용중/여유/수리중/폐기/분실)
- **상태별 자산 분포**: 도넛(Doughnut) 차트로 상태별 비율 시각화
- **카테고리별 자산 수**: 바(Bar) 차트로 카테고리별 자산 수량 비교
- **최근 활동 목록**: 최근 등록/배정/반납 활동 타임라인 (최근 10건)
- **월별 등록 추이**: 최근 12개월간 신규 등록 자산 수 라인 차트

### 2.2 카테고리별 현황

#### 2.2.1 하드웨어 현황

- 하드웨어 유형별(서버/네트워크/데스크톱/노트북/모니터/프린터/스캐너/기타) 보유/사용중/여유 현황 테이블
- 유형별 사용률(사용중/전체) 표시
- 노후 장비 현황 (구매일 기준 3년/5년 이상 경과 자산)

#### 2.2.2 소프트웨어 라이선스 현황

- 라이선스 유형별 총 보유 수 / 사용중 수 / 여유 수
- 라이선스 만료 임박 목록 (30일 이내 만료 예정)
- 라이선스 사용률 시각화 (프로그레스 바)

### 2.3 부서별 자산 현황

- 부서별 배정 자산 총 수
- 부서별 카테고리 분포 (하드웨어/소프트웨어 비율)
- 부서 인원 대비 1인당 자산 수 (부서 인원은 `01-03` 조직도 모듈에서 조회)
- 부서별 자산 가치(구매가 기준) 합산

### 2.4 보증 만료 현황

- **30일 이내 만료**: 긴급 대응이 필요한 자산 목록 (빨강 표시)
- **90일 이내 만료**: 사전 대응이 필요한 자산 목록 (주황 표시)
- **이미 만료**: 보증이 만료된 자산 목록
- 보증 만료 알림 기능:
  - 30일 전, 7일 전 자동 알림 (자산 관리자에게)
  - 대시보드 상단 알림 배너로 표시

### 2.5 자산 감가상각 (선택, 참고용)

- **정액법** 기준 잔존가치 계산:
  - `잔존가치 = 취득가액 - (취득가액 × 경과연수 / 내용연수)`
  - 내용연수 기본값: 하드웨어 5년, 소프트웨어 3년 (카테고리별 설정 가능)
  - 잔존가치가 0 이하인 경우 0으로 표시
- 자산 장부가액 현황 테이블: 취득가, 감가상각 누계, 잔존가치
- 카테고리별 총 자산가치 요약

### 2.6 엑셀 내보내기

다음 리포트를 엑셀(.xlsx) 파일로 내보내기한다:

| 리포트명 | 포함 항목 |
|----------|-----------|
| 전체 자산 목록 | 자산번호, 분류, 자산명, 제조사, 모델, S/N, 상태, 위치, 구매일, 구매가, 보증만료일 |
| 부서별 현황 | 부서명, 자산 수, 카테고리별 수량, 총 자산가치 |
| 배정 현황 | 자산번호, 자산명, 배정대상, 배정유형, 배정일, 확인여부 |
| 보증 만료 현황 | 자산번호, 자산명, 구매일, 보증만료일, 남은일수, 상태 |
| 감가상각 현황 | 자산번호, 자산명, 취득가, 내용연수, 경과연수, 감가상각누계, 잔존가치 |

- 엑셀 파일 생성은 서버 사이드에서 수행 (openpyxl 라이브러리 사용)
- 대량 데이터 내보내기 시 비동기 처리 후 다운로드 링크 제공

---

## 3. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 대시보드 전체 로딩 시간 2초 이내 (자산 1만 건 기준) |
| 성능 | 리포트 조회 응답시간 1초 이내 |
| 성능 | 엑셀 내보내기 1만 건 기준 10초 이내 |
| 캐싱 | 대시보드 요약 데이터는 5분 캐시 적용 (Redis 또는 인메모리) |
| 보안 | 리포트 조회는 자산 관리자 또는 부서 관리자 권한 필요 |
| 보안 | 부서 관리자는 본인 부서 리포트만 조회 가능 |
| 확장성 | 차트 라이브러리는 shadcn/ui Charts 사용 (Recharts 기반 래퍼) |
| 접근성 | 차트에 대체 텍스트(alt text) 및 데이터 테이블 병행 제공 |

---

## 4. 데이터베이스 스키마

> 리포트 모듈은 `05-01`, `05-02`에서 정의한 테이블을 기반으로 집계 쿼리를 수행하므로 별도의 신규 테이블은 최소화한다. 감가상각 설정용 테이블만 추가한다.

### 4.1 `asset_depreciation_settings` (감가상각 설정)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 설정 고유 식별자 |
| `category_id` | `UUID` | NOT NULL, FK → `asset_categories.id`, UNIQUE | 카테고리 ID |
| `useful_life_years` | `SMALLINT` | NOT NULL | 내용연수 (년) |
| `residual_value_rate` | `NUMERIC(5,4)` | NOT NULL, DEFAULT `0.0000` | 잔존가치율 (0.0000 ~ 1.0000) |
| `depreciation_method` | `VARCHAR(20)` | NOT NULL, DEFAULT `'STRAIGHT_LINE'` | 감가상각 방법 |
| `created_by` | `UUID` | NOT NULL | 생성자 ID |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | 생성 일시 (UTC) |
| `updated_by` | `UUID` | NULLABLE | 수정자 ID |
| `updated_at` | `TIMESTAMPTZ` | NULLABLE | 수정 일시 (UTC) |

**CHECK 제약조건**:
- `chk_useful_life` CHECK (`useful_life_years` > 0)
- `chk_residual_value_rate` CHECK (`residual_value_rate` >= 0 AND `residual_value_rate` <= 1)
- `chk_depreciation_method` CHECK (`depreciation_method` IN (`'STRAIGHT_LINE'`))

**기본 설정값**:

| 카테고리 | 내용연수 | 잔존가치율 |
|----------|----------|-----------|
| 서버 | 5년 | 0% |
| 네트워크 장비 | 5년 | 0% |
| 데스크톱 | 5년 | 0% |
| 노트북 | 5년 | 0% |
| 모니터 | 5년 | 0% |
| 프린터 | 5년 | 0% |
| 스캐너 | 5년 | 0% |
| 기타 주변기기 | 3년 | 0% |
| OS 라이선스 | 3년 | 0% |
| 오피스 라이선스 | 3년 | 0% |
| 개발도구 라이선스 | 3년 | 0% |
| 기타 소프트웨어 | 3년 | 0% |

### 4.2 리포트 집계용 주요 뷰 (참고)

실제 뷰(View) 생성 여부는 성능 테스트 후 결정하며, 아래는 주요 집계 쿼리의 논리 구조이다.

#### `v_asset_summary` (자산 요약 뷰)

```sql
SELECT
    status,
    COUNT(*) AS asset_count,
    SUM(purchase_price) AS total_value
FROM assets
WHERE deleted_at IS NULL
GROUP BY status;
```

#### `v_asset_by_category` (카테고리별 현황 뷰)

```sql
SELECT
    c.id AS category_id,
    c.name AS category_name,
    c.code AS category_code,
    a.status,
    COUNT(*) AS asset_count
FROM assets a
JOIN asset_categories c ON a.category_id = c.id
WHERE a.deleted_at IS NULL
GROUP BY c.id, c.name, c.code, a.status;
```

#### `v_asset_by_department` (부서별 현황 뷰)

```sql
SELECT
    aa.assignee_id AS department_id,
    COUNT(DISTINCT aa.asset_id) AS assigned_count,
    SUM(a.purchase_price) AS total_value
FROM asset_assignments aa
JOIN assets a ON aa.asset_id = a.id
WHERE aa.assignee_type = 'DEPARTMENT'
  AND aa.is_active = TRUE
  AND a.deleted_at IS NULL
GROUP BY aa.assignee_id;
```

#### `v_warranty_expiring` (보증 만료 임박 뷰)

```sql
SELECT
    id, asset_number, name, manufacturer, model,
    warranty_expires_at,
    (warranty_expires_at - CURRENT_DATE) AS days_remaining
FROM assets
WHERE deleted_at IS NULL
  AND status NOT IN ('DISPOSED', 'LOST')
  AND warranty_expires_at IS NOT NULL
  AND warranty_expires_at <= CURRENT_DATE + INTERVAL '90 days'
ORDER BY warranty_expires_at ASC;
```

---

## 5. API 명세

### 5.1 자산 요약 리포트

#### `GET /api/v1/assets/report/summary`

전체 자산 현황 요약을 조회한다.

**응답 (200 OK)**:

```json
{
  "data": {
    "total_count": 523,
    "total_value": 1284500000,
    "by_status": [
      { "status": "IN_USE", "label": "사용중", "count": 342, "value": 856200000 },
      { "status": "AVAILABLE", "label": "여유", "count": 98, "value": 215800000 },
      { "status": "IN_REPAIR", "label": "수리중", "count": 15, "value": 32500000 },
      { "status": "DISPOSED", "label": "폐기", "count": 62, "value": 168000000 },
      { "status": "LOST", "label": "분실", "count": 6, "value": 12000000 }
    ],
    "monthly_registrations": [
      { "month": "2025-04", "count": 12 },
      { "month": "2025-05", "count": 8 },
      { "month": "2025-06", "count": 15 },
      { "month": "2025-07", "count": 5 },
      { "month": "2025-08", "count": 9 },
      { "month": "2025-09", "count": 11 },
      { "month": "2025-10", "count": 7 },
      { "month": "2025-11", "count": 14 },
      { "month": "2025-12", "count": 6 },
      { "month": "2026-01", "count": 18 },
      { "month": "2026-02", "count": 10 },
      { "month": "2026-03", "count": 22 }
    ],
    "recent_activities": [
      {
        "type": "REGISTERED",
        "asset_number": "NB-2026-042",
        "asset_name": "개발팀 노트북 #42",
        "performed_by": "관리자",
        "performed_at": "2026-03-23T09:00:00Z"
      },
      {
        "type": "ASSIGNED",
        "asset_number": "MON-2026-055",
        "asset_name": "27인치 모니터",
        "detail": "→ 김개발 (개발팀)",
        "performed_by": "관리자",
        "performed_at": "2026-03-22T14:00:00Z"
      },
      {
        "type": "RETURNED",
        "asset_number": "NB-2025-033",
        "asset_name": "이전 노트북",
        "detail": "김개발 → 반납 (교체)",
        "performed_by": "관리자",
        "performed_at": "2026-03-22T13:30:00Z"
      }
    ]
  }
}
```

### 5.2 카테고리별 리포트

#### `GET /api/v1/assets/report/by-category`

카테고리별 자산 현황을 조회한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `parent_category_id` | `UUID` | N | 상위 카테고리 ID (미지정 시 대분류 기준) |

**응답 (200 OK)**:

```json
{
  "data": [
    {
      "category_id": "uuid-svr",
      "category_name": "서버",
      "category_code": "SVR",
      "total_count": 45,
      "in_use_count": 38,
      "available_count": 5,
      "in_repair_count": 2,
      "disposed_count": 0,
      "utilization_rate": 0.844,
      "total_value": 450000000,
      "aging": {
        "under_3_years": 30,
        "3_to_5_years": 10,
        "over_5_years": 5
      }
    },
    {
      "category_id": "uuid-nb",
      "category_name": "노트북",
      "category_code": "NB",
      "total_count": 180,
      "in_use_count": 155,
      "available_count": 18,
      "in_repair_count": 7,
      "disposed_count": 0,
      "utilization_rate": 0.861,
      "total_value": 540000000,
      "aging": {
        "under_3_years": 120,
        "3_to_5_years": 45,
        "over_5_years": 15
      }
    },
    {
      "category_id": "uuid-sos",
      "category_name": "OS 라이선스",
      "category_code": "SOS",
      "total_count": 200,
      "in_use_count": 175,
      "available_count": 25,
      "in_repair_count": 0,
      "disposed_count": 0,
      "utilization_rate": 0.875,
      "total_value": 60000000,
      "license_expiring_30d": 5,
      "license_expiring_90d": 12
    }
  ]
}
```

### 5.3 부서별 리포트

#### `GET /api/v1/assets/report/by-department`

부서별 자산 배정 현황을 조회한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `department_id` | `UUID` | N | 특정 부서 필터 (미지정 시 전체 부서) |

**응답 (200 OK)**:

```json
{
  "data": [
    {
      "department_id": "uuid-dept-dev",
      "department_name": "개발팀",
      "member_count": 25,
      "total_assigned": 68,
      "per_person_average": 2.72,
      "by_category": [
        { "category_name": "노트북", "count": 25 },
        { "category_name": "모니터", "count": 25 },
        { "category_name": "기타 주변기기", "count": 18 }
      ],
      "total_value": 125000000
    },
    {
      "department_id": "uuid-dept-design",
      "department_name": "디자인팀",
      "member_count": 10,
      "total_assigned": 35,
      "per_person_average": 3.50,
      "by_category": [
        { "category_name": "데스크톱", "count": 10 },
        { "category_name": "모니터", "count": 15 },
        { "category_name": "기타 주변기기", "count": 10 }
      ],
      "total_value": 85000000
    },
    {
      "department_id": "uuid-dept-infra",
      "department_name": "인프라팀",
      "member_count": 8,
      "total_assigned": 22,
      "per_person_average": 2.75,
      "by_category": [
        { "category_name": "노트북", "count": 8 },
        { "category_name": "모니터", "count": 8 },
        { "category_name": "기타 주변기기", "count": 6 }
      ],
      "total_value": 45000000
    }
  ]
}
```

### 5.4 보증 만료 리포트

#### `GET /api/v1/assets/report/warranty-expiring`

보증 만료 임박 자산 목록을 조회한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `days` | `integer` | N | 만료까지 남은 일수 (기본값: 90) |
| `include_expired` | `boolean` | N | 이미 만료된 자산 포함 여부 (기본값: `false`) |
| `category_id` | `UUID` | N | 카테고리 필터 |
| `page` | `integer` | N | 페이지 번호 (기본값: 1) |
| `size` | `integer` | N | 페이지 크기 (기본값: 20) |

**응답 (200 OK)**:

```json
{
  "data": {
    "summary": {
      "expiring_30d": 8,
      "expiring_90d": 23,
      "already_expired": 15
    },
    "items": [
      {
        "id": "uuid-asset-10",
        "asset_number": "SVR-2024-005",
        "name": "웹서버 #5",
        "category": { "name": "서버", "code": "SVR" },
        "manufacturer": "Dell",
        "model": "PowerEdge R750",
        "warranty_expires_at": "2026-04-05",
        "days_remaining": 13,
        "urgency": "HIGH",
        "status": "IN_USE",
        "current_assignee": "인프라팀"
      },
      {
        "id": "uuid-asset-22",
        "asset_number": "NB-2023-078",
        "name": "경영지원팀 노트북 #78",
        "category": { "name": "노트북", "code": "NB" },
        "manufacturer": "Lenovo",
        "model": "ThinkPad X1 Carbon",
        "warranty_expires_at": "2026-05-15",
        "days_remaining": 53,
        "urgency": "MEDIUM",
        "status": "IN_USE",
        "current_assignee": "박경영 (경영지원팀)"
      }
    ]
  },
  "pagination": {
    "page": 1,
    "size": 20,
    "total_count": 23,
    "total_pages": 2
  }
}
```

**`urgency` 기준**:
- `HIGH`: 30일 이내 만료
- `MEDIUM`: 31~90일 이내 만료
- `EXPIRED`: 이미 만료

### 5.5 감가상각 리포트

#### `GET /api/v1/assets/report/depreciation`

자산 감가상각 현황을 조회한다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `category_id` | `UUID` | N | 카테고리 필터 |
| `page` | `integer` | N | 페이지 번호 (기본값: 1) |
| `size` | `integer` | N | 페이지 크기 (기본값: 20) |

**응답 (200 OK)**:

```json
{
  "data": {
    "summary": {
      "total_acquisition_value": 1284500000,
      "total_depreciation": 456200000,
      "total_book_value": 828300000
    },
    "items": [
      {
        "id": "uuid-asset-42",
        "asset_number": "NB-2026-042",
        "name": "개발팀 노트북 #42",
        "category_name": "노트북",
        "purchase_date": "2026-03-15",
        "purchase_price": 3990000,
        "useful_life_years": 5,
        "elapsed_years": 0.02,
        "depreciation_amount": 15960,
        "book_value": 3974040,
        "depreciation_rate": 0.004
      },
      {
        "id": "uuid-asset-10",
        "asset_number": "SVR-2024-005",
        "name": "웹서버 #5",
        "category_name": "서버",
        "purchase_date": "2024-01-10",
        "purchase_price": 15000000,
        "useful_life_years": 5,
        "elapsed_years": 2.20,
        "depreciation_amount": 6600000,
        "book_value": 8400000,
        "depreciation_rate": 0.440
      }
    ]
  },
  "pagination": {
    "page": 1,
    "size": 20,
    "total_count": 461,
    "total_pages": 24
  }
}
```

### 5.6 엑셀 내보내기

#### `GET /api/v1/assets/report/export`

리포트 데이터를 엑셀 파일로 내보낸다.

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `format` | `string` | Y | 내보내기 형식 (`xlsx`) |
| `type` | `string` | Y | 리포트 유형 |
| `category_id` | `UUID` | N | 카테고리 필터 |
| `department_id` | `UUID` | N | 부서 필터 |

**`type` 가능한 값**:

| 값 | 설명 |
|----|------|
| `all_assets` | 전체 자산 목록 |
| `by_department` | 부서별 현황 |
| `assignments` | 배정 현황 |
| `warranty` | 보증 만료 현황 |
| `depreciation` | 감가상각 현황 |

**요청 예시**:

```
GET /api/v1/assets/report/export?format=xlsx&type=all_assets
GET /api/v1/assets/report/export?format=xlsx&type=by_department&department_id=uuid-dept-dev
GET /api/v1/assets/report/export?format=xlsx&type=warranty
```

**응답 (200 OK)**:
- `Content-Type`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition`: `attachment; filename="asset_report_all_assets_20260323.xlsx"`
- 본문: 엑셀 파일 바이너리

**에러 응답 (400 Bad Request)**:

```json
{
  "error": {
    "code": "INVALID_EXPORT_TYPE",
    "message": "지원하지 않는 리포트 유형입니다. 가능한 값: all_assets, by_department, assignments, warranty, depreciation"
  }
}
```

> **대용량 내보내기 (1만 건 이상)**: 비동기 처리로 전환하며, 완료 시 다운로드 URL을 반환한다. (향후 구현)

---

## 6. 화면 설계

### 6.1 자산 대시보드 (`/inventories/dashboard`)

```
┌─────────────────────────────────────────────────────────────────┐
│ 자산 현황 대시보드                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚠ 보증 만료 임박: 8건의 자산이 30일 이내 보증 만료 예정 [확인하기]  │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │
│  │ 전체 자산  │ │  사용중   │ │   여유    │ │  수리중   │ │ 폐기  │ │
│  │   523     │ │   342    │ │    98    │ │    15    │ │  62  │ │
│  │          │ │  65.4%   │ │  18.7%   │ │   2.9%   │ │11.9% │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘ │
│                                                                 │
│  ┌─ 상태별 분포 ──────────────┐ ┌─ 카테고리별 자산 수 ─────────┐ │
│  │                            │ │                              │ │
│  │      ┌───────┐             │ │  노트북     ████████████ 180 │ │
│  │     ╱ 사용중  ╲            │ │  모니터     ████████░░░ 120  │ │
│  │    │  65.4%   │            │ │  서버       ███░░░░░░░  45  │ │
│  │    │          │            │ │  데스크톱   ██░░░░░░░░  30  │ │
│  │     ╲  여유  ╱             │ │  네트워크   ██░░░░░░░░  25  │ │
│  │      └───────┘             │ │  프린터     █░░░░░░░░░  15  │ │
│  │   수리중 ■  폐기 ■         │ │  SW라이선스 ████████░░░ 108 │ │
│  │                            │ │                              │ │
│  └────────────────────────────┘ └──────────────────────────────┘ │
│                                                                 │
│  ┌─ 월별 등록 추이 (최근 12개월) ───────────────────────────────┐ │
│  │                                          ●                  │ │
│  │                              ●          ╱                   │ │
│  │        ●                    ╱ ╲    ●   ╱                    │ │
│  │  ●    ╱ ╲       ●    ●    ╱   ╲  ╱ ╲ ╱                     │ │
│  │   ╲  ╱   ╲     ╱ ╲  ╱╲  ╱     ╲╱                           │ │
│  │    ╲╱     ╲   ╱   ╲╱  ╲╱                                   │ │
│  │            ╲ ╱                                              │ │
│  │             ●                                               │ │
│  │  4   5   6   7   8   9  10  11  12   1   2   3             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─ 최근 활동 ──────────────────────────────────────────────┐   │
│  │ 03-23 09:00  등록   NB-2026-042 개발팀 노트북 #42  관리자 │   │
│  │ 03-22 14:00  배정   MON-2026-055 → 김개발         관리자 │   │
│  │ 03-22 13:30  반납   NB-2025-033 ← 김개발 (교체)   관리자 │   │
│  │ 03-22 10:00  상태변경 PRT-2025-008 여유→수리중     관리자 │   │
│  │ 03-21 16:00  등록   MON-2026-055 27인치 모니터     관리자 │   │
│  │                                         [전체 보기 →]    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

- 상단: 보증 만료 임박 경고 배너 (30일 이내 만료 자산이 있을 때만 표시)
- 요약 카드: 숫자 클릭 시 해당 상태의 자산 목록 페이지로 이동
- 차트: 도넛 차트(상태별), 바 차트(카테고리별), 라인 차트(월별 추이)
- 최근 활동: 타임라인 형식, [전체 보기]로 전체 이력 페이지 이동

### 6.2 상세 리포트 테이블 (`/inventories/reports/{type}`)

```
┌─────────────────────────────────────────────────────────────────┐
│ 부서별 자산 현황                                     [엑셀 다운로드]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 필터: [부서 선택 ▼]  [카테고리 ▼]            [필터 적용] [초기화]  │
│                                                                 │
│ ┌──────────┬──────┬──────┬──────┬──────┬──────┬───────────────┐│
│ │ 부서명    │ 인원 │ 자산수│노트북│모니터 │기타  │ 총 자산가치    ││
│ ├──────────┼──────┼──────┼──────┼──────┼──────┼───────────────┤│
│ │ 개발팀    │  25  │  68  │  25  │  25  │  18  │ 125,000,000원 ││
│ │ 디자인팀  │  10  │  35  │  -   │  15  │  10  │  85,000,000원 ││
│ │ 인프라팀  │   8  │  22  │   8  │   8  │   6  │  45,000,000원 ││
│ │ 경영지원팀│  15  │  38  │  15  │  15  │   8  │  62,000,000원 ││
│ │ 영업팀    │  20  │  42  │  20  │  12  │  10  │  78,000,000원 ││
│ ├──────────┼──────┼──────┼──────┼──────┼──────┼───────────────┤│
│ │ 합계      │  78  │ 205  │  68  │  75  │  52  │ 395,000,000원 ││
│ └──────────┴──────┴──────┴──────┴──────┴──────┴───────────────┘│
│                                                                 │
│ 1인당 평균 자산: 2.63건   1인당 평균 자산가치: 5,064,103원          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

- 정렬: 컬럼 헤더 클릭으로 오름차순/내림차순 전환
- 필터: 부서, 카테고리별 필터 적용
- 합계 행: 테이블 하단에 전체 합계 표시
- [엑셀 다운로드] 클릭 시 현재 필터 조건의 데이터를 엑셀로 내보내기

### 6.3 보증 만료 알림 목록 (`/inventories/reports/warranty`)

```
┌─────────────────────────────────────────────────────────────────┐
│ 보증 만료 현황                                       [엑셀 다운로드]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ 30일 이내 │  │ 90일 이내 │  │ 이미 만료 │                      │
│  │  🔴 8건   │  │  🟠 23건  │  │  ⚫ 15건  │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
│                                                                 │
│ 필터: [카테고리 ▼] [긴급도 ▼]                     [검색 🔍]       │
│                                                                 │
│ ┌──────┬──────────┬────────┬────────┬────────┬──────┬────────┐ │
│ │ 긴급 │ 자산번호  │ 자산명  │ 만료일  │ 남은일수│ 상태 │ 배정자  │ │
│ ├──────┼──────────┼────────┼────────┼────────┼──────┼────────┤ │
│ │ 🔴   │SVR-24-005│웹서버#5│04-05   │  13일  │사용중│인프라팀 │ │
│ │ 🔴   │NB-23-012 │영업팀..│04-10   │  18일  │사용중│이영업   │ │
│ │ 🔴   │MON-23-044│회의실..│04-15   │  23일  │사용중│경영지원 │ │
│ │ 🟠   │NB-23-078 │경영지..│05-15   │  53일  │사용중│박경영   │ │
│ │ 🟠   │PRT-23-003│3층프..│05-22   │  60일  │사용중│디자인팀 │ │
│ │ 🟠   │SVR-24-008│DB서..│06-10   │  79일  │사용중│인프라팀 │ │
│ └──────┴──────────┴────────┴────────┴────────┴──────┴────────┘ │
│                                                                 │
│ 총 23건                                  < 1  2 >               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

- 상단 요약 카드: 긴급도별 건수 표시
- 긴급도별 색상 코드: 빨강(30일 이내), 주황(90일 이내), 검정(이미 만료)
- 남은일수 기준 오름차순 정렬 (가장 급한 것부터)
- 자산번호 클릭 시 자산 상세 페이지로 이동

### 6.4 엑셀 다운로드

- 각 리포트 화면 우측 상단에 [엑셀 다운로드] 버튼 배치
- 클릭 시 현재 화면의 필터 조건이 반영된 데이터를 엑셀로 내보내기
- 다운로드 진행 중 로딩 스피너 표시
- 다운로드 완료 시 토스트 알림: "파일이 다운로드되었습니다."
- 파일명 형식: `asset_report_{type}_{YYYYMMDD}.xlsx`
  - 예: `asset_report_all_assets_20260323.xlsx`

---

## 7. 인수 조건

### 7.1 대시보드

- [ ] 전체 자산 수와 상태별 자산 수가 카드형 요약으로 표시된다.
- [ ] 상태별 자산 분포가 도넛 차트로 시각화된다.
- [ ] 카테고리별 자산 수가 바 차트로 시각화된다.
- [ ] 최근 12개월간 월별 등록 추이가 라인 차트로 표시된다.
- [ ] 최근 등록/배정/반납 활동 10건이 타임라인으로 표시된다.
- [ ] 대시보드 로딩 시간이 2초 이내이다.

### 7.2 카테고리별 현황

- [ ] 하드웨어 유형별 보유/사용중/여유/수리중/폐기 현황이 테이블로 표시된다.
- [ ] 유형별 사용률(사용중/전체)이 계산되어 표시된다.
- [ ] 노후 장비 현황(3년 이상/5년 이상)이 표시된다.
- [ ] 소프트웨어 라이선스의 만료 임박 건수가 표시된다.

### 7.3 부서별 현황

- [ ] 부서별 배정 자산 수가 테이블로 표시된다.
- [ ] 부서별 카테고리 분포가 표시된다.
- [ ] 1인당 자산 수가 계산되어 표시된다 (부서 인원 연동).
- [ ] 부서별 자산 가치(구매가 기준) 합산이 표시된다.

### 7.4 보증 만료 현황

- [ ] 30일 이내 만료 자산이 빨강으로 표시된다.
- [ ] 90일 이내 만료 자산이 주황으로 표시된다.
- [ ] 이미 만료된 자산을 포함/제외하여 조회할 수 있다.
- [ ] 대시보드에 보증 만료 임박 경고 배너가 표시된다.
- [ ] 남은 일수 기준으로 정렬된다.

### 7.5 감가상각

- [ ] 정액법 기준으로 자산별 잔존가치가 계산된다.
- [ ] 카테고리별 내용연수를 설정할 수 있다.
- [ ] 총 취득가, 감가상각 누계, 총 잔존가치가 요약으로 표시된다.

### 7.6 엑셀 내보내기

- [ ] 전체 자산 목록을 엑셀 파일로 내보낼 수 있다.
- [ ] 부서별 현황을 엑셀 파일로 내보낼 수 있다.
- [ ] 배정 현황을 엑셀 파일로 내보낼 수 있다.
- [ ] 보증 만료 현황을 엑셀 파일로 내보낼 수 있다.
- [ ] 감가상각 현황을 엑셀 파일로 내보낼 수 있다.
- [ ] 내보내기 시 현재 필터 조건이 반영된다.
- [ ] 파일명에 리포트 유형과 날짜가 포함된다.

---

## 8. 참고사항

- 대시보드 성능 최적화를 위해 집계 결과를 캐싱한다. Redis를 사용하여 5분 TTL로 캐싱하며, 자산 등록/수정/삭제/배정/반납 시 관련 캐시를 무효화한다.
- 부서 인원 정보는 `01-03` 조직도 모듈의 API를 호출하여 조회한다. 대시보드 로딩 시 병렬 호출로 성능을 최적화한다.
- 엑셀 생성은 Python `openpyxl` 라이브러리를 사용한다. 셀 서식(숫자 포맷, 날짜 포맷, 헤더 스타일)을 적용하여 가독성을 높인다.
- 감가상각 계산은 참고용이며, 실제 회계 처리 시에는 ERP 시스템의 값을 기준으로 해야 한다. 법적 효력이 없음을 UI에 명시한다.
- 차트 라이브러리는 `shadcn/ui Charts` (Recharts 기반 래퍼)를 사용한다. shadcn/ui의 테마와 일관된 스타일을 제공하며 Next.js와 호환성이 좋다.
- 보증 만료 알림은 별도 배치 작업(Cron Job)으로 매일 오전 9시에 실행하여, 만료 30일 전/7일 전 자산에 대해 자산 관리자에게 알림을 발송한다. 알림 모듈과의 연동은 향후 구현한다.
- 리포트 API의 응답이 대용량인 경우, 스트리밍 응답(`StreamingResponse`)을 사용하여 메모리 사용량을 최적화한다.
- 향후 확장 고려사항:
  - PDF 형식 리포트 내보내기
  - 자산 TCO(Total Cost of Ownership) 분석
  - 자산 교체 주기 예측 리포트
  - 이메일 기반 정기 리포트 발송 (주간/월간)
