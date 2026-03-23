# 아론티어 그룹웨어

사내 업무 효율화를 위한 그룹웨어 시스템.

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프론트엔드 | Next.js 16 + TypeScript + shadcn/ui + Tailwind CSS |
| 백엔드 | Python FastAPI + SQLAlchemy 2.0 |
| 데이터베이스 | SQLite (개발용, PostgreSQL 전환 가능) |
| 인증 | JWT (access token + refresh token) |

## 시작하기

### 사전 요구사항

- Python 3.12+
- Node.js 20+
- npm

### 백엔드

```bash
cd backend

# 가상환경 생성 및 활성화
python3.12 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (시드 데이터 자동 생성)
python -m uvicorn app.main:app --reload --port 8000
```

API 문서: http://localhost:8000/docs

### 테스트 데이터 (Fixture) 로드

시드 데이터만으로는 대시보드가 비어 보입니다. 3개월치 출퇴근, 결재, 자산 등의 테스트 데이터를 로드하려면:

```bash
cd backend
source venv/bin/activate
python -m fixtures.load_fixtures
```

### 프론트엔드

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev -- --port 3000
```

http://localhost:3000 접속

## 로그인

| 계정 | 이메일 | 비밀번호 |
|------|--------|----------|
| 관리자 | admin@arontier.co | admin1234! |
| 김개발 | dev.kim@arontier.co | password123! |
| 박디자인 | design.park@arontier.co | password123! |
| 이영업 | sales.lee@arontier.co | password123! |
| 정인사 | hr.jung@arontier.co | password123! |
| 최총무 | ga.choi@arontier.co | password123! |
| 한인프라 | infra.han@arontier.co | password123! |

## 모듈

- **인증 / 조직도** — 로그인, 사용자 관리, 부서·직급·직책 트리, RBAC
- **전자결재** — 기안, 결재선(순차/병렬), 승인·반려, 대시보드
- **게시판** — 공지사항(고정/필독), 자유게시판, 첨부파일, 댓글
- **근태관리** — 출퇴근 기록, 휴가 신청(근로기준법 연차), 초과근무(주 52시간)
- **자산관리** — 자산 등록·분류, 배정·반납, 현황 리포트

## 프로젝트 구조

```
├── tasks/                  # 모듈별 태스크 명세 (마크다운)
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # API 엔드포인트
│   │   ├── models/             # SQLAlchemy 모델
│   │   ├── schemas/            # Pydantic 스키마
│   │   ├── core/               # 설정, DB, 인증, 의존성
│   │   └── utils/              # 시드 데이터
│   ├── fixtures/               # 테스트 데이터 (JSON + 로더)
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/                # Next.js 페이지 (App Router)
        ├── components/         # shadcn/ui + 커스텀 컴포넌트
        └── lib/                # API 클라이언트, 인증 컨텍스트
```
