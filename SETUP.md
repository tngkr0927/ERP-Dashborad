# ERP Dashboard — 처음부터 세팅하기

Docker를 처음 쓰는 사람 기준으로 작성한 가이드.

---

## Step 1. Docker Desktop 설치

Docker = 내 컴퓨터 안에 가상 서버를 만들어주는 도구.
이걸 쓰면 PostgreSQL, Python, Node.js를 따로 설치할 필요 없이 한 번에 실행됨.

### Windows

1. https://www.docker.com/products/docker-desktop 접속
2. **Download for Windows** 클릭 → 설치 파일 실행
3. 설치 중 **"Use WSL 2 instead of Hyper-V"** 체크 (권장)
4. 설치 완료 후 **재부팅**
5. Docker Desktop 앱 실행 → 고래 아이콘이 트레이에 뜨면 준비 완료

### Mac

1. https://www.docker.com/products/docker-desktop 접속
2. 본인 칩에 맞는 버전 다운로드 (Apple Silicon / Intel)
3. `.dmg` 파일 열어서 Applications에 드래그
4. Docker Desktop 실행 → 상단바에 고래 아이콘 뜨면 준비 완료

### 설치 확인

터미널(또는 명령 프롬프트)을 열고:

```bash
docker --version
# → Docker version 27.x.x 같은 게 나오면 성공

docker compose version
# → Docker Compose version v2.x.x 같은 게 나오면 성공
```

> 안 되면 Docker Desktop이 실행 중인지 확인. 고래 아이콘이 떠 있어야 함.

---

## Step 2. 프로젝트 다운로드

```bash
git clone <repo-url>
cd ERP-Dashborad
```

> Git이 없으면 https://git-scm.com 에서 설치.
> 또는 GitHub에서 ZIP 다운로드 → 압축 풀어도 됨.

---

## Step 3. 실행 (이것만 하면 끝)

```bash
docker compose up --build
```

처음 실행하면 필요한 것들을 자동으로 다운받아서 시간이 좀 걸림 (2~5분).
터미널에 로그가 쭉 올라가고, 아래 비슷한 메시지가 보이면 성공:

```
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend-1  | VITE v5.x.x  ready in xxx ms
```

### 접속 확인

브라우저에서 열어보기:

| 주소 | 뭐가 보이면 성공 |
|------|----------------|
| http://localhost:3000 | 대시보드 화면 |
| http://localhost:8000/docs | API 문서 (Swagger) |
| http://localhost:8000/health | `{"status":"ok"}` |

---

## Step 4. 종료

터미널에서 `Ctrl + C` 누르면 멈춤.

완전히 정리하려면:

```bash
docker compose down
```

---

## 그 다음부터는

### 다시 실행할 때

```bash
cd ERP-Dashborad
docker compose up
```

> 코드를 수정했으면 `docker compose up --build` (build 붙이기)

### 자주 쓰는 명령어

| 하고 싶은 것 | 명령어 |
|-------------|--------|
| 실행 | `docker compose up` |
| 코드 수정 후 실행 | `docker compose up --build` |
| 백그라운드로 실행 | `docker compose up -d` |
| 종료 | `docker compose down` |
| 로그 보기 | `docker compose logs -f` |
| 백엔드 로그만 보기 | `docker compose logs -f backend` |
| DB 데이터 초기화 | `docker compose down -v` |
| 실행 중인 서비스 확인 | `docker compose ps` |

---

## 잘 안 될 때

### "port is already allocated"

다른 프로그램이 같은 포트를 쓰고 있음.

```bash
# Mac/Linux — 어떤 프로그램이 쓰고 있는지 확인
lsof -i :5432
lsof -i :8000
lsof -i :3000

# Windows
netstat -ano | findstr :5432
```

해당 프로그램을 끄거나, Docker Desktop에서 기존 컨테이너를 Stop.

### "Cannot connect to the Docker daemon"

Docker Desktop이 안 켜져 있음. Docker Desktop 앱을 먼저 실행.

### 처음 실행인데 너무 오래 걸림

이미지 다운로드 중. 인터넷 속도에 따라 첫 실행은 5~10분 걸릴 수 있음.
두 번째부터는 캐시돼서 빠름.

### DB 연결 에러 (backend 로그에 "connection refused")

DB가 아직 준비 안 됐을 수 있음. `docker compose down` 후 다시 `docker compose up --build`.

---

## 참고: 이 프로젝트에서 Docker가 하는 일

`docker compose up` 한 줄이 내부적으로 하는 것:

```
1. PostgreSQL 16 서버를 띄움 (포트 5432)
2. Python 환경을 만들고 pip install 후 FastAPI 서버를 띄움 (포트 8000)
3. Node.js 환경을 만들고 npm install 후 React 개발 서버를 띄움 (포트 3000)
4. 백엔드가 DB 준비될 때까지 자동으로 기다림
5. 프론트엔드의 /api 요청을 자동으로 백엔드로 전달 (프록시)
```

즉, Python, Node.js, PostgreSQL을 내 컴퓨터에 직접 설치하지 않아도
Docker가 격리된 환경에서 알아서 설치하고 실행해줌.
