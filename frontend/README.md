# Crypto Portfolio Tracker

DeBank 스타일의 온체인 데이터 대시보드 + 포트폴리오 트래커

![Portfolio Dashboard](Screenshot%202026-01-02%20080438.png)

## 주요 기능

### Portfolio
- **멀티체인 지원**: Ethereum, BSC, Polygon, Arbitrum, Optimism, Avalanche, Base
- **온체인 자동 조회**: 지갑 주소 입력 시 토큰 잔액 자동 수집 (Moralis API)
- **체인별 파이차트**: 자산 분배 도넛 차트 시각화
- **토큰 상세 차트**: 토큰 클릭 → 캔들스틱 차트 (1D/7D/14D/30D)
- **실시간 가격**: Binance WebSocket 연동 (Live 배지)

### DeFi
- **프로토콜 TVL**: 상위 50개 DeFi 프로토콜 TVL 순위
- **체인 TVL**: 전체 체인별 TVL 분포 차트
- **실시간 데이터**: DefiLlama API 연동

## 기술 스택

| 카테고리 | 기술 |
|---------|------|
| Frontend | React 19 + Vite + TypeScript |
| Styling | Tailwind CSS v4 + shadcn/ui |
| State | Zustand + TanStack Query |
| Charts | ApexCharts |
| Realtime | Binance WebSocket |

## 설치 및 실행

### 1. 의존성 설치

```bash
cd crypto-portfolio
npm install
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일:
```env
# Moralis API Key (필수)
# https://admin.moralis.io/ 에서 발급
VITE_MORALIS_API_KEY=your_moralis_api_key

# CoinGecko API Key (선택, 차트 기능용)
# https://www.coingecko.com/en/api 에서 발급
VITE_COINGECKO_API_KEY=your_coingecko_demo_key
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

### 4. 프로덕션 빌드

```bash
npm run build
npm run preview
```

## API 키 발급

### Moralis (필수)

1. https://admin.moralis.io/ 가입
2. "Create new project" 클릭
3. Settings → API Keys → Web3 API Key 복사

### CoinGecko (선택)

1. https://www.coingecko.com/en/api 가입
2. Dashboard → API Keys → Demo Key 생성

### 무료 API (키 불필요)

- **DefiLlama**: DeFi TVL 데이터
- **Binance WebSocket**: 실시간 가격

## 사용 방법

1. **지갑 조회**: 상단 검색창에 EVM 지갑 주소 입력 (0x...)
2. **Portfolio 탭**: 체인별 자산 분포, 토큰 목록 확인
3. **토큰 클릭**: 캔들스틱 차트로 가격 추이 확인
4. **DeFi 탭**: 전체 DeFi 프로토콜 TVL 순위 확인
5. **새로고침**: 우측 상단 버튼으로 데이터 갱신

## 프로젝트 구조

```
src/
├── components/
│   ├── ui/                 # shadcn/ui 컴포넌트
│   ├── charts/             # 차트 컴포넌트
│   │   ├── ChainPieChart.tsx
│   │   └── TokenCandlestick.tsx
│   ├── defi/               # DeFi 컴포넌트
│   │   ├── ProtocolList.tsx
│   │   └── ChainTVL.tsx
│   ├── Dashboard.tsx       # 메인 대시보드
│   ├── TokenDetailModal.tsx
│   └── ...
├── hooks/
│   ├── usePortfolio.ts     # 포트폴리오 데이터
│   ├── useTokenChart.ts    # 차트 데이터
│   ├── useDefi.ts          # DeFi 데이터
│   └── useRealtimePrice.ts # 실시간 가격
├── services/
│   ├── moralis.ts          # Moralis API
│   ├── coingecko.ts        # CoinGecko API
│   ├── defillama.ts        # DefiLlama API
│   └── websocket/          # Binance WebSocket
├── store/
│   ├── portfolioStore.ts
│   └── realtimeStore.ts
└── types/
    ├── index.ts
    └── defi.ts
```

## API 사용량

| API | 무료 한도 | 용도 |
|-----|----------|------|
| Moralis | 40K CU/일 | 토큰 잔액 조회 |
| CoinGecko | 30 calls/분 | 가격 차트 |
| DefiLlama | 무제한 | DeFi TVL |
| Binance WS | 무제한 | 실시간 가격 |

## 라이선스

MIT
