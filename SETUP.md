# ERP Dashboard — 로컬 환경 세팅 가이드

---

## 사전 준비 (필수 설치)

| 도구 | 버전 | 확인 명령 |
|------|------|----------|
| Git | - | `git --version` |
| Docker & Docker Compose | Docker 20+ | `docker --version && docker compose version` |
| Python | 3.11+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| npm | 9+ | `npm --version` |

> Docker만 쓸 거면 Python, Node.js 설치 안 해도 됨.

---

## 방법 1: Docker Compose (권장)

가장 간단. DB + 백엔드 + 프론트엔드 한 번에 뜸.

```bash
# 1. 레포 클론
git clone <repo-url>
cd ERP-Dashborad

# 2. 실행
docker compose up --build

# 3. 접속
# 프론트엔드: http://localhost:3000
# 백엔드 API: http://localhost:8000
# Swagger 문서: http://localhost:8000/docs
# DB: localhost:5432 (erp_user / erp_pass)
```

```bash
# 종료
docker compose down

# DB 데이터까지 삭제하고 싶을 때
docker compose down -v
```

---

## 방법 2: 로컬 직접 실행 (개발용)

Docker 없이 각각 직접 띄우는 방법. 디버깅할 때 편함.

### 2-1. PostgreSQL 준비

**옵션 A — Docker로 DB만 띄우기 (추천)**
```bash
docker run -d \
  --name erp-db \
  -e POSTGRES_USER=erp_user \
  -e POSTGRES_PASSWORD=erp_pass \
  -e POSTGRES_DB=erp_dashboard \
  -p 5432:5432 \
  postgres:16-alpine
```

**옵션 B — 로컬 PostgreSQL 사용**
```bash
# PostgreSQL 설치 후
psql -U postgres

CREATE USER erp_user WITH PASSWORD 'erp_pass';
CREATE DATABASE erp_dashboard OWNER erp_user;
\q
```

### 2-2. 백엔드

```bash
cd backend

# 가상환경 생성 & 활성화
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://erp_user:erp_pass@localhost:5432/erp_dashboard
DATABASE_URL_SYNC=postgresql+psycopg2://erp_user:erp_pass@localhost:5432/erp_dashboard
EOF

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

> 서버 시작 시 테이블 자동 생성됨 (`main.py`의 `lifespan`에서 처리)

### 2-3. 프론트엔드

```bash
cd frontend

# 패키지 설치
npm install

# 서버 실행
npm run dev
```

> Vite 프록시 설정(`vite.config.ts`)이 `/api` 요청을 `backend:8000`으로 보냄.
> 로컬 실행 시에는 프록시 target을 `http://localhost:8000`으로 바꿔야 함:

```ts
// frontend/vite.config.ts — 로컬 개발 시 수정
proxy: {
  "/api": {
    target: "http://localhost:8000",  // backend:8000 → localhost:8000
    changeOrigin: true,
  },
},
```

---

## 동작 확인 체크리스트

```bash
# 1. 헬스체크
curl http://localhost:8000/health
# → {"status":"ok"}

# 2. 데이터 업로드 테스트
curl -X POST http://localhost:8000/api/upload \
  -H "Content-Type: application/json" \
  -d '{"source_system": "test", "payload": {"name": "테스트", "value": 100}}'
# → {"id":1,"message":"Data uploaded successfully"}

# 3. 분석 실행
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_type": "dummy"}'
# → {"id":1,"analysis_type":"dummy","result_data":{...}}

# 4. 대시보드 조회
curl http://localhost:8000/api/dashboard
# → {"results":[...]}

# 5. 프론트엔드
# 브라우저에서 http://localhost:3000 접속
```

---

## 자주 쓰는 명령어

| 상황 | 명령어 |
|------|--------|
| Docker 전체 실행 | `docker compose up --build` |
| Docker 백그라운드 실행 | `docker compose up -d --build` |
| Docker 로그 보기 | `docker compose logs -f backend` |
| Docker 종료 | `docker compose down` |
| DB 초기화 (데이터 삭제) | `docker compose down -v` |
| 백엔드만 재시작 | `docker compose restart backend` |
| DB 직접 접속 | `docker exec -it erp-db psql -U erp_user -d erp_dashboard` |
| Swagger 문서 | 브라우저에서 `http://localhost:8000/docs` |

---

## 트러블슈팅

**포트 충돌** — 5432, 8000, 3000 포트가 이미 쓰이고 있으면:
```bash
# 어떤 프로세스가 쓰고 있는지 확인
lsof -i :5432
# 해당 프로세스 종료 후 재시도
```

**DB 연결 실패** — `connection refused` 에러:
- Docker 방식: `docker compose ps`로 db 서비스가 healthy인지 확인
- 로컬 방식: `.env` 파일의 `localhost` 확인, PostgreSQL 서비스 실행 확인

**프론트엔드 API 호출 실패** — 로컬 실행 시 `vite.config.ts`의 proxy target이 `localhost:8000`인지 확인
