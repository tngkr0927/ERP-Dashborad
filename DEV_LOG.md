# ERP Analytics Dashboard — 개발 기록

> 요청 → 구현 내용을 누적 기록. 나중에 복습용.

---

## #1. 프로젝트 초기 세팅 (2026-02-12)

**요청:** ERP 데이터 분석 대시보드의 확장 가능한 기본 골격 구축

### 기술 스택

| 영역 | 선택 | 이유 |
|------|------|------|
| Backend | FastAPI | async, 자동 Swagger |
| DB | PostgreSQL + JSONB | 데이터 구조 미정 → JSONB로 유연하게 |
| ORM | SQLAlchemy 2.0 (async) | Alembic 마이그레이션 연계 |
| Frontend | React + TypeScript + TailwindCSS | 컴포넌트 기반, 타입 안전 |
| 차트 | Recharts | React 전용, 러닝커브 낮음 |
| 인프라 | Docker Compose | 원커맨드 실행 |

### 구현 내용

**DB** — `raw_data_logs`(원본 저장), `analysis_results`(분석 결과) 테이블. JSONB 컬럼으로 스키마 변경 없이 다양한 데이터 수용.

**분석기** — 전략 패턴 적용. `BaseAnalyzer` 추상 클래스를 상속해 새 분석기를 만들고 `ANALYZER_REGISTRY`에 등록하면 끝.

**API** — 4개 엔드포인트:
- `POST /api/upload` → 원본 데이터 저장
- `POST /api/analyze` → 분석 실행
- `GET /api/dashboard` → 결과 조회
- `GET /health` → 상태 확인

**프론트엔드** — Sidebar + Header + 콘텐츠 영역 레이아웃. 2x2 그리드 위젯(Placeholder).

**Docker** — db / backend / frontend 3개 서비스. `docker-compose up --build`로 실행.

### 확장 가이드

| 하고 싶은 것 | 수정할 파일 |
|-------------|------------|
| 새 분석 로직 | `backend/app/services/analyzer.py` |
| 차트 추가 | `frontend/src/components/` |
| 새 API | `backend/app/api/routes.py` |
| DB 스키마 변경 | `backend/app/models/erp.py` |

---

*개발 진행 시 새 섹션 추가*
