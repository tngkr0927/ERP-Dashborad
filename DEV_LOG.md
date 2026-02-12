# ERP Analytics Dashboard — 개발 기록

> 실제 개발 과정과 구현 내용만 기록. 질문/답변 기록은 `QNA_LOG.md` 참고.

---

## #1. 프로젝트 초기 세팅 (2026-02-12)

### 기술 스택

| 영역 | 선택 | 이유 |
|------|------|------|
| Backend | FastAPI | async 지원, 자동 Swagger 생성 |
| DB | PostgreSQL + JSONB | 데이터 구조 미정 → JSONB로 유연하게 |
| ORM | SQLAlchemy 2.0 (async) | Alembic 마이그레이션 연계 |
| Frontend | React + TypeScript + TailwindCSS | 컴포넌트 기반, 타입 안전 |
| 차트 | Recharts | React 전용, 러닝커브 낮음 |
| 인프라 | Docker Compose | 원커맨드 실행 |

### 구현된 것

**DB 모델** (`backend/app/models/erp.py`)
- `raw_data_logs` — 원본 데이터 저장. `payload`를 JSONB로 받아서 스키마 변경 없이 다양한 데이터 수용
- `analysis_results` — 분석 결과 저장. 마찬가지로 `result_data`가 JSONB

**분석 엔진** (`backend/app/services/analyzer.py`)
- 전략 패턴 적용. `BaseAnalyzer` 추상 클래스 → 새 분석기는 상속 후 `ANALYZER_REGISTRY`에 등록
- 기본 제공: `DummyAnalyzer` (테스트용)

**API 엔드포인트** (`backend/app/api/routes.py`)
- `POST /api/upload` → 원본 데이터 저장
- `POST /api/analyze` → 분석 실행
- `GET /api/dashboard` → 결과 조회
- `GET /health` → 상태 확인

**프론트엔드** (`frontend/src/`)
- Sidebar + Header + 콘텐츠 영역 레이아웃
- 2x2 그리드 위젯 (Placeholder)
- `/api` 요청은 Vite 프록시로 백엔드에 전달

**Docker** (`docker-compose.yml`)
- `db` — PostgreSQL 16 Alpine
- `backend` — Python 3.11 + FastAPI
- `frontend` — Node 20 + React dev server
- 헬스체크로 DB 준비 대기 후 백엔드 시작

### 파일 구조

```
ERP-Dashborad/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 앱, lifespan에서 테이블 자동생성
│   │   ├── database.py          # async 엔진 & 세션
│   │   ├── models/erp.py        # SQLAlchemy 모델
│   │   ├── schemas/erp.py       # Pydantic 스키마
│   │   ├── api/routes.py        # API 라우터
│   │   └── services/analyzer.py # 분석 엔진 (전략 패턴)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # 메인 레이아웃
│   │   ├── components/          # Sidebar, Header, DashboardGrid
│   │   └── services/api.ts      # API 호출 함수
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── SETUP.md                     # 환경 세팅 가이드
└── QNA_LOG.md                   # 질문/답변 기록
```

---

## #2. 문서 정비 (2026-02-12)

### SETUP.md

- 초기 버전: Docker + 로컬 실행 두 가지 방법 병렬 안내
- 개선 버전: Docker 초보 기준으로 전면 재작성
  - Docker Desktop 설치부터 안내 (Windows/Mac)
  - `docker compose up --build` 한 줄 실행 중심
  - 트러블슈팅 4가지 케이스 추가

### 개발 기록 분리

- `DEV_LOG.md` — 순수 개발 내용만 (이 파일)
- `QNA_LOG.md` — 질문/답변/이유 기록 (신규)

---

*개발 진행 시 새 섹션 추가*
