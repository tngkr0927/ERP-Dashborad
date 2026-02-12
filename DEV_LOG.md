# ERP Analytics Dashboard — 개발 기록

> 이 문서는 **요청 사항 → 설계 결정 → 구현 내용**을 누적 기록합니다.
> 나중에 코드를 다시 볼 때 "왜 이렇게 만들었지?"를 빠르게 파악하기 위한 용도입니다.

---

## #1. 프로젝트 스캐폴딩 & 아키텍처 구축

**날짜:** 2026-02-12

### 요청 내용 (What was asked)

- 사내 ERP 데이터를 수집 → 저장 → 분석 → 시각화하는 웹 대시보드를 만들고 싶다.
- 아직 **구체적인 데이터 항목, 분석 로직, 차트 종류가 전혀 정해지지 않은 상태**.
- 그래서 나중에 뭐든 갈아끼울 수 있는 **확장 가능한 기본 골격(Boilerplate)** 을 먼저 잡아달라.

### 기술 스택 선택 이유 (Why this stack)

| 영역 | 선택 | 이유 |
|------|------|------|
| Backend | **FastAPI** (Python) | 비동기(async) 기본 지원, 자동 Swagger 문서 생성, 타입 힌트 기반 검증 |
| DB | **PostgreSQL + JSONB** | 데이터 구조가 미정이므로, 정형(컬럼) + 비정형(JSONB)을 동시에 쓸 수 있는 PostgreSQL이 적합 |
| ORM | **SQLAlchemy 2.0** (async) | Python 표준 ORM, async 지원, 마이그레이션(Alembic)과 궁합이 좋음 |
| 분석 | **Pandas** | Python 데이터 분석의 사실상 표준 라이브러리 |
| Frontend | **React + TypeScript** | 컴포넌트 기반 UI, 타입 안전성 확보 |
| 스타일 | **TailwindCSS** | 유틸리티 클래스 방식으로 빠른 프로토타이핑 가능 |
| 차트 | **Recharts** | React 전용, 선언형 API, 러닝커브 낮음 |
| 인프라 | **Docker Compose** | 한 줄(`docker-compose up`)로 DB+백엔드+프론트엔드 동시 실행 |

### 구현 내용 상세 (What was built)

#### A. 데이터베이스 설계

```
raw_data_logs 테이블
├── id            (PK, auto increment)
├── created_at    (timestamptz, 자동 생성)
├── source_system (varchar 100) — ERP 시스템 출처 구분용
└── payload       (JSONB) — 원본 데이터 통째로 저장

analysis_results 테이블
├── id            (PK, auto increment)
├── analyzed_at   (timestamptz, 자동 생성)
├── analysis_type (varchar 100) — 어떤 분석을 돌렸는지 구분
└── result_data   (JSONB) — 분석 결과 통째로 저장
```

**핵심 포인트 — JSONB를 쓴 이유:**
- 아직 ERP 데이터의 필드가 확정되지 않았음
- JSONB에 넣으면 `{"매출액": 1000, "부서": "영업"}` 같은 형태를 스키마 변경 없이 저장 가능
- 나중에 데이터 구조가 확정되면 자주 쓰는 필드를 별도 컬럼으로 뽑아내면 됨

**관련 파일:** `backend/app/models/erp.py`

---

#### B. 백엔드 — 전략 패턴(Strategy Pattern)으로 분석기 설계

```
BaseAnalyzer (추상 클래스)
│   analyze(data: DataFrame) -> dict  ← 이 메서드만 구현하면 됨
│
├── DummyAnalyzer (구현체 #1)
│     → 데이터 건수만 세서 리턴 (시스템 동작 테스트용)
│
├── (미래) SalesTrendAnalyzer
├── (미래) CostAnalyzer
└── (미래) ...
```

**전략 패턴이란?**
- 알고리즘(분석 로직)을 **인터페이스 뒤에 숨기고**, 실행 시점에 원하는 구현체를 골라 쓰는 디자인 패턴
- 새 분석 로직을 추가할 때 기존 코드를 수정하지 않고 **새 클래스만 만들면 됨** (개방-폐쇄 원칙, OCP)

**분석기 등록 방법 (`ANALYZER_REGISTRY`):**
```python
# backend/app/services/analyzer.py 하단

ANALYZER_REGISTRY: dict[str, BaseAnalyzer] = {
    "dummy": DummyAnalyzer(),
    # TODO: 여기에 새 분석기를 추가
    # "sales_trend": SalesTrendAnalyzer(),
}
```

**관련 파일:** `backend/app/services/analyzer.py`

---

#### C. 백엔드 — API 엔드포인트

| Method | 경로 | 역할 | 입력 | 출력 |
|--------|------|------|------|------|
| `POST` | `/api/upload` | 원본 데이터 저장 | `{ source_system, payload }` | `{ id, message }` |
| `POST` | `/api/analyze` | 분석 실행 & 결과 저장 | `{ analysis_type, source_system? }` | `{ id, analysis_type, result_data }` |
| `GET` | `/api/dashboard` | 최신 분석 결과 조회 | `?limit=10` | `{ results: [...] }` |
| `GET` | `/health` | 서버 상태 확인 | - | `{ status: "ok" }` |

**데이터 흐름:**
```
ERP 시스템 --[JSON]--> POST /api/upload ---> raw_data_logs 테이블
                                                     │
                        POST /api/analyze <──────────┘
                              │
                              ├── DB에서 데이터 로드
                              ├── Pandas DataFrame 변환
                              ├── Analyzer.analyze() 실행
                              └── 결과 → analysis_results 테이블
                                                     │
                        GET /api/dashboard <─────────┘
                              │
                              └── 프론트엔드로 JSON 전달
```

**관련 파일:** `backend/app/api/routes.py`

---

#### D. 프론트엔드 — 레이아웃 구조

```
┌─────────────────────────────────────────────┐
│  Sidebar (w-56)  │        Header (h-14)     │
│                  │──────────────────────────│
│  - 대시보드       │                          │
│  - 데이터 업로드   │   ┌────────┐ ┌────────┐  │
│  - 분석 실행      │   │ 위젯 A  │ │ 위젯 B  │  │
│  - 설정          │   │(준비중) │ │(준비중) │  │
│                  │   └────────┘ └────────┘  │
│                  │   ┌────────┐ ┌────────┐  │
│                  │   │ 위젯 C  │ │ 위젯 D  │  │
│                  │   │(준비중) │ │(준비중) │  │
│                  │   └────────┘ └────────┘  │
└─────────────────────────────────────────────┘
```

**컴포넌트 계층:**
```
App.tsx
└── DashboardLayout         ← 전체 셸 (사이드바 + 헤더 + 콘텐츠 영역)
    ├── Sidebar             ← 좌측 네비게이션
    ├── Header              ← 상단 바
    └── DashboardPage       ← 메인 콘텐츠
        └── PlaceholderWidget × 4  ← 빈 위젯 (2×2 CSS Grid)
```

**관련 파일:**
- 레이아웃: `frontend/src/layouts/`
- 위젯: `frontend/src/components/PlaceholderWidget.tsx`
- 페이지: `frontend/src/pages/DashboardPage.tsx`
- API 연동: `frontend/src/services/api.ts`

---

#### E. Docker Compose — 서비스 구성

```yaml
services:
  db:        # PostgreSQL 16 — 포트 5432
  backend:   # FastAPI (uvicorn) — 포트 8000, DB 연결 대기 후 시작
  frontend:  # Vite dev server — 포트 3000, /api → backend 프록시
```

**실행 명령:** `docker-compose up --build`

---

### 나중에 확장할 때 참고 (TODO 가이드)

| 하고 싶은 것 | 수정할 파일 | 방법 |
|-------------|------------|------|
| 새 분석 로직 추가 | `backend/app/services/analyzer.py` | `BaseAnalyzer` 상속 → `ANALYZER_REGISTRY`에 등록 |
| 실제 차트 추가 | `frontend/src/components/PlaceholderWidget.tsx` | Recharts 컴포넌트로 교체 |
| 대시보드 위젯 변경 | `frontend/src/pages/DashboardPage.tsx` | `widgets` 배열 수정 또는 직접 컴포넌트 배치 |
| 새 API 추가 | `backend/app/api/routes.py` | `router`에 새 엔드포인트 추가 |
| DB 스키마 변경 | `backend/app/models/erp.py` | 모델 수정 후 Alembic 마이그레이션 |

---

### 프로젝트 파일 트리

```
ERP-Dashborad/
├── docker-compose.yml
├── .gitignore
├── DEV_LOG.md              ← 이 파일 (개발 기록)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI 앱 진입점
│       ├── config.py           # 환경변수 설정
│       ├── database.py         # SQLAlchemy 엔진/세션
│       ├── models/
│       │   └── erp.py          # DB 모델 (raw_data_logs, analysis_results)
│       ├── services/
│       │   └── analyzer.py     # 분석기 (BaseAnalyzer, DummyAnalyzer)
│       └── api/
│           └── routes.py       # API 라우터
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── App.tsx
        ├── main.tsx
        ├── index.css
        ├── layouts/
        │   ├── DashboardLayout.tsx
        │   ├── Sidebar.tsx
        │   └── Header.tsx
        ├── components/
        │   └── PlaceholderWidget.tsx
        ├── pages/
        │   └── DashboardPage.tsx
        └── services/
            └── api.ts
```

---

*이 문서는 개발이 진행될 때마다 새로운 섹션이 추가됩니다.*
