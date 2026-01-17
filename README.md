# Crypto Tracker

멀티체인 **지갑 추적** + **컨트랙트 분석** + **포트폴리오 대시보드** 올인원 프로젝트

## 구조

```
crypto-tracker/
├── backend/           # Python 텔레그램 봇 + API
│   ├── bot/           # 텔레그램 핸들러
│   ├── webhook/       # FastAPI 서버 (인증 지원)
│   ├── services/      # 외부 API 연동
│   │   ├── price_service.py   # CoinGecko 실시간 가격
│   │   └── http_client.py     # HTTP 클라이언트 풀링
│   ├── utils/         # 유틸리티
│   │   ├── validators.py      # 주소 검증
│   │   └── signature.py       # 웹훅 서명 검증
│   ├── analyzers/     # 컨트랙트 분석기
│   └── main.py
└── frontend/          # React 웹 대시보드
    ├── src/
    │   ├── services/  # API 연동 (Moralis, DefiLlama, Binance WS)
    │   └── components/
    └── dist/          # 빌드 결과물
```

---

## 기능 상세

### 1. 텔레그램 봇

#### 지갑 추적
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/add <체인> <주소> <라벨>` | 지갑 추가 + 스트림 자동 생성 | `/add eth 0x123...abc whale1` |
| `/list` | 추적 중인 지갑 목록 (상태 포함) | - |
| `/remove <라벨>` | 지갑 삭제 + 스트림 자동 삭제 | `/remove whale1` |
| `/toggle <라벨>` | Incoming 알림 ON/OFF 전환 | `/toggle whale1` |
| `/filter <라벨> <금액>` | 최소 알림 금액 설정 (USD) | `/filter whale1 1000` |
| `/chains` | 지원 체인 목록 | - |

**동작 방식:**
- 지갑 추가 시 Moralis(EVM) / Helius(Solana) 스트림을 자동 생성
- 스트림 생성 실패 시 DB 저장 안함 (데이터 일관성 유지)
- 주소 검증: EVM 체크섬, Solana Base58 검증
- 중복 체크: 같은 사용자의 라벨/주소 중복 방지

#### 컨트랙트 분석 (자동 감지)
봇에 주소만 보내면 자동 분석 시작:

```
# EVM 주소 입력 시
0xdAC17F958D2ee523a2206206994597C13D831ec7
→ 체인 선택 버튼 표시 (ETH, BSC, Arbitrum, Base 등)
→ 선택한 체인에서 분석 실행

# Solana 주소 입력 시
EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
→ 즉시 Solana 분석 실행
```

**분석 항목:**
| 카테고리 | 데이터 소스 | 제공 정보 |
|---------|------------|----------|
| 기본 정보 | Web3 RPC | 이름, 심볼, 데시멀, 총 공급량 |
| 보안 분석 | GoPlus Security | 허니팟, 민트 가능, 오너 권한, 세금 등 |
| 시장 정보 | DEXScreener | 가격, 유동성, 거래량, 가격 변동률 |
| 컨트랙트 | Etherscan | 검증 여부, 컴파일러 버전, 소스 공개 |

**위험도 등급:**
| 등급 | 설명 |
|------|------|
| LOW | 위험 항목 없음 |
| MEDIUM | 1~2개 위험 항목 |
| HIGH | 3~4개 위험 항목 |
| CRITICAL | 허니팟 또는 셀프디스트럭트 감지 |

---

### 2. 웹훅 서버 (FastAPI)

#### 엔드포인트

| 경로 | 메서드 | 인증 | 설명 |
|------|--------|------|------|
| `/health` | GET | - | 헬스 체크 |
| `/webhook/moralis` | POST | X-Signature 헤더 | EVM 트랜잭션 수신 |
| `/webhook/helius` | POST | ?auth= 쿼리 | Solana 트랜잭션 수신 |
| `/` | GET | - | 대시보드 (활성화 시) |

#### 보안 검증

**Moralis 웹훅:**
```
1. X-Signature 헤더에서 서명 추출
2. Keccak-256(body + API_KEY)로 서명 계산
3. 서명 일치 여부 검증
4. 실패 시 401 Unauthorized
```

**Helius 웹훅:**
```
1. URL 쿼리에서 auth 토큰 추출 (?auth=xxx)
2. HELIUS_WEBHOOK_SECRET과 비교
3. 실패 시 401 Unauthorized
```

#### 트랜잭션 알림 포맷
```
[IN/OUT] 체인명
라벨: whale1
금액: 1.5 ETH ($3,500.00)
From: 0x123...abc
To: 0x456...def
TX: [View on Etherscan]
```

---

### 3. 웹 대시보드 (React)

#### Portfolio 탭
| 기능 | 설명 |
|------|------|
| 총 자산 | 모든 체인 합산 USD 가치 |
| 체인별 요약 | ETH, BSC, Polygon 등 체인별 자산 |
| 토큰 그리드 | 보유 토큰 카드 (가격, 수량, 가치) |
| 체인 분포 | 파이차트로 체인별 비중 시각화 |
| 토큰 상세 | 클릭 시 캔들차트 + 상세 정보 모달 |

#### DeFi 탭
| 기능 | 설명 |
|------|------|
| 프로토콜 목록 | TVL 상위 DeFi 프로토콜 순위 |
| 체인 TVL | 체인별 총 TVL 비교 |

#### 실시간 기능
| 기능 | 연동 | 설명 |
|------|------|------|
| 실시간 가격 | Binance WebSocket | 보유 토큰 가격 자동 업데이트 |
| 연결 상태 | - | Live 배지로 연결 상태 표시 |
| 자동 갱신 | React Query | 1분 staleTime, 자동 refetch |

---

## 주요 특징

### 보안
- **Moralis 웹훅 서명 검증** - Keccak-256 해시
- **Helius 인증 토큰 검증** - 쿼리 파라미터 방식
- **EVM 주소 체크섬 검증** - 잘못된 주소 필터링
- **Solana Base58 검증** - 유효한 공개키 확인
- **Path Traversal 방어** - 대시보드 정적 파일 서빙 시

### 성능
- **HTTP 클라이언트 풀링** - 연결 재사용으로 지연 감소
- **가격 캐싱** - CoinGecko 5분 TTL
- **WebSocket 참조 카운트** - 메모리 누수 방지
- **병렬 API 호출** - asyncio.gather로 분석 속도 향상

### 안정성
- **Graceful Shutdown** - SIGTERM/SIGINT 처리
- **웹훅 전용 모드** - 봇 토큰 없어도 실행 가능
- **API 재시도** - tenacity로 지수 백오프 재시도
- **에러 격리** - 개별 API 실패해도 다른 데이터 표시

---

## 빠른 시작

### 1. Backend 설정

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env 편집
```

### 2. Frontend 빌드 (대시보드 사용시)

```bash
cd frontend
npm install
npm run build
```

### 3. 실행

```bash
cd backend
source .venv/bin/activate
python main.py
```

---

## 환경 변수

### Backend (.env)

```env
# 텔레그램 (선택 - 없으면 웹훅 서버만 실행)
TELEGRAM_BOT_TOKEN=your_token

# 지갑 추적 (EVM)
MORALIS_API_KEY=your_key

# 지갑 추적 (Solana)
HELIUS_API_KEY=your_key
HELIUS_WEBHOOK_SECRET=your_secret  # 웹훅 인증용

# 서버
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000

# 대시보드
DASHBOARD_ENABLED=true
DASHBOARD_PATH=../frontend/dist

# 로깅
LOG_LEVEL=INFO
```

### Frontend (.env)

```env
VITE_MORALIS_API_KEY=your_key
```

---

## 지원 체인

| 체인 | 지갑 추적 | 컨트랙트 분석 | 대시보드 |
|------|:--------:|:------------:|:-------:|
| Ethereum | O | O | O |
| BSC | O | O | O |
| Polygon | O | - | O |
| Arbitrum | O | O | O |
| Base | O | O | O |
| Optimism | O | - | O |
| Avalanche | O | - | O |
| Solana | O | O | - |

---

## API 연동 현황

| 서비스 | 용도 | 필수 여부 |
|--------|------|:--------:|
| Moralis | EVM 지갑 추적, 포트폴리오 조회 | O (EVM 사용 시) |
| Helius | Solana 지갑 추적 | O (Solana 사용 시) |
| GoPlus | 토큰 보안 분석 | 선택 |
| DEXScreener | 토큰 시장 정보 | 선택 |
| CoinGecko | 실시간 토큰 가격 | 선택 |
| DefiLlama | DeFi TVL 정보 | 선택 |
| Binance | WebSocket 실시간 가격 | 선택 |

---

## 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# Helius 웹훅 테스트 (인증 토큰 포함)
curl -X POST "http://localhost:8000/webhook/helius?auth=your_secret" \
  -H "Content-Type: application/json" \
  -d '[{"type":"TRANSFER","nativeTransfers":[]}]'
```

---

## 라이선스

MIT
