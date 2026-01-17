# 🚀 Crypto Tracker - 시작 가이드

암호화폐 지갑 추적 + 웹 대시보드 프로그램입니다.

---

## 📋 목차

1. [처음 시작하기 (필수)](#1-처음-시작하기-필수)
2. [웹 대시보드 켜는 방법](#2-웹-대시보드-켜는-방법)
3. [텔레그램 봇 세팅](#3-텔레그램-봇-세팅)
4. [문제 해결](#4-문제-해결)

---

## 1. 처음 시작하기 (필수)

### STEP 1: 프로그램 준비하기

터미널(cmd 또는 terminal)을 열고 프로젝트 폴더로 이동:

```bash
cd /home/user/coding/wallet-tracker-bot
```

### STEP 2: Python 가상환경 만들기

이미 만들어져 있으면 스킵해도 됩니다.

```bash
cd backend
python3 -m venv .venv
```

### STEP 3: 가상환경 켜기

**리눅스/맥:**
```bash
source .venv/bin/activate
```

**윈도우:**
```bash
.venv\Scripts\activate
```

성공하면 터미널 앞에 `(.venv)`가 보입니다.

### STEP 4: 필요한 프로그램 설치

```bash
pip install -r requirements.txt
```

설치가 끝나면 준비 완료!

---

## 2. 웹 대시보드 켜는 방법

웹 대시보드는 크롬/엣지 같은 브라우저에서 볼 수 있는 화면입니다.

### STEP 1: 프론트엔드 빌드하기

**처음 1번만 하면 됩니다!**

새 터미널 창을 열고:

```bash
cd frontend
npm install
npm run build
```

`dist` 폴더가 생성됩니다. 이게 웹 화면 파일입니다.

### STEP 2: 대시보드 켜기 설정

`backend` 폴더에 `.env` 파일을 만듭니다:

```bash
cd backend
cp .env.example .env
```

`.env` 파일을 텍스트 에디터로 열고 **2줄만 수정**:

```env
DASHBOARD_ENABLED=true
DASHBOARD_PATH=../frontend/dist
```

- `DASHBOARD_ENABLED=false` → `true`로 변경
- `# DASHBOARD_PATH=...` → 맨 앞 `#` 지우기

저장하고 닫기!

### STEP 3: 프로그램 실행

가상환경이 켜진 상태에서:

```bash
cd backend
source .venv/bin/activate  # 가상환경 안 켜져있으면 실행
python main.py
```

### STEP 4: 브라우저로 접속

주소창에 입력:

```
http://localhost:8000
```

웹 대시보드가 보이면 성공! 🎉

**종료하려면:** 터미널에서 `Ctrl+C`

---

## 3. 텔레그램 봇 세팅

텔레그램으로 지갑을 추적하고 알림을 받을 수 있습니다.

### STEP 1: 텔레그램 봇 토큰 받기

1. 텔레그램 앱 실행
2. `@BotFather` 검색해서 대화 시작
3. `/newbot` 입력
4. 봇 이름 입력 (예: `My Crypto Tracker`)
5. 봇 사용자명 입력 (예: `mycrypto_bot`, 반드시 `bot`으로 끝나야 함)
6. 토큰 복사 (예: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### STEP 2: API 키 받기 (선택사항)

지갑 추적하려면 필요합니다:

**Moralis (이더리움, BSC 등):**
1. https://admin.moralis.io/ 접속
2. 무료 회원가입
3. API Key 복사

**Helius (솔라나):**
1. https://helius.dev/ 접속
2. 무료 회원가입
3. API Key 복사

### STEP 3: .env 파일 수정

`backend/.env` 파일을 열고 수정:

```env
# 필수: 텔레그램 봇 토큰 입력
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# 선택: API 키 입력 (지갑 추적할 거면 필요)
MORALIS_API_KEY=여기에_모랄리스_키_붙여넣기
HELIUS_API_KEY=여기에_헬리우스_키_붙여넣기

# 대시보드 (이미 했으면 그대로)
DASHBOARD_ENABLED=true
DASHBOARD_PATH=../frontend/dist

# 서버 설정 (기본값 그대로 두기)
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
```

저장!

### STEP 4: 봇 실행

```bash
cd backend
source .venv/bin/activate
python main.py
```

터미널에 이런 메시지가 보이면 성공:

```
Crypto Tracker Bot Starting...
Telegram bot started...
Webhook server started on port 8000
```

### STEP 5: 텔레그램에서 봇 테스트

1. 텔레그램에서 내 봇 검색 (`@mycrypto_bot`)
2. `/start` 입력
3. 봇이 응답하면 성공! 🎉

**주요 명령어:**
- `/add eth 지갑주소 이름` - 지갑 추가
- `/list` - 내 지갑 목록 보기
- `/chains` - 지원하는 체인 보기

---

## 4. 문제 해결

### 웹 대시보드가 안 보여요

**체크리스트:**
1. `frontend` 폴더에 `dist` 폴더가 있나요?
   - 없으면: `cd frontend && npm run build`
2. `.env` 파일에 `DASHBOARD_ENABLED=true`인가요?
3. `python main.py` 실행했나요?
4. 주소가 `http://localhost:8000`이 맞나요?

### "ModuleNotFoundError" 에러가 나요

가상환경을 안 켰거나 패키지를 안 설치했습니다:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

### 텔레그램 봇이 응답을 안 해요

1. `.env` 파일에 `TELEGRAM_BOT_TOKEN`이 제대로 입력됐나요?
2. `python main.py` 실행 중인가요?
3. 터미널에 에러 메시지가 있나요? 있으면 복사해서 검색해보세요.

### npm 명령어가 안 돼요

Node.js가 설치 안 돼있습니다:

1. https://nodejs.org/ 접속
2. LTS 버전 다운로드
3. 설치 후 터미널 재시작
4. `npm --version` 입력해서 버전이 나오면 성공

---

## 📚 더 자세한 정보

### 지원 체인

- Ethereum (ETH)
- BSC (BNB)
- Polygon (MATIC)
- Arbitrum
- Base
- Optimism
- Avalanche
- Solana

### 프로그램 구조

```
wallet-tracker-bot/
├── backend/           # Python 서버 + 텔레그램 봇
│   ├── main.py       # 메인 실행 파일
│   ├── .env          # 설정 파일 (직접 만들어야 함)
│   └── requirements.txt
└── frontend/          # 웹 대시보드
    ├── dist/         # 빌드된 웹 파일 (npm run build로 생성)
    └── package.json
```

### 완전히 처음부터 다시 시작하기

```bash
# 1. 모든 프로그램 종료 (Ctrl+C)

# 2. 가상환경 삭제
cd backend
rm -rf .venv

# 3. 프론트엔드 빌드 삭제
cd ../frontend
rm -rf dist node_modules

# 4. 처음부터 다시
cd ..
# 이제 위의 "1. 처음 시작하기"부터 다시 따라하기
```

---

## 💡 팁

- **한 번만 빌드하면 됨**: `npm run build`는 코드 수정 안 했으면 다시 안 해도 됨
- **가상환경은 항상 켜기**: `python main.py` 실행 전에 `source .venv/bin/activate`
- **터미널 2개 사용**: 하나는 봇 실행용, 하나는 명령어 입력용
- **로그 확인**: 에러 나면 터미널 메시지를 잘 읽어보기

---

## 📞 도움이 필요하면

1. 에러 메시지를 복사해서 구글에 검색
2. GitHub Issues에 질문 올리기
3. 터미널에 나온 로그를 같이 첨부하기

**즐거운 코딩하세요! 🚀**
