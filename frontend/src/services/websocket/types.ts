// Binance WebSocket 메시지 타입

// 24시간 티커 (개별)
export interface BinanceTicker {
  e: string;      // 이벤트 타입 '24hrTicker'
  E: number;      // 이벤트 시간
  s: string;      // 심볼 (BTCUSDT)
  p: string;      // 가격 변동
  P: string;      // 가격 변동률 (%)
  w: string;      // 가중평균가
  c: string;      // 현재가 (종가)
  Q: string;      // 마지막 거래 수량
  o: string;      // 시가
  h: string;      // 고가
  l: string;      // 저가
  v: string;      // 거래량 (베이스)
  q: string;      // 거래량 (쿼트)
  O: number;      // 통계 시작 시간
  C: number;      // 통계 종료 시간
  F: number;      // 첫 거래 ID
  L: number;      // 마지막 거래 ID
  n: number;      // 총 거래 수
}

// 미니 티커
export interface BinanceMiniTicker {
  e: string;      // '24hrMiniTicker'
  E: number;      // 이벤트 시간
  s: string;      // 심볼
  c: string;      // 현재가
  o: string;      // 시가
  h: string;      // 고가
  l: string;      // 저가
  v: string;      // 거래량 (베이스)
  q: string;      // 거래량 (쿼트)
}

// 캔들스틱 (Kline)
export interface BinanceKline {
  e: string;      // 'kline'
  E: number;      // 이벤트 시간
  s: string;      // 심볼
  k: {
    t: number;    // 캔들 시작 시간
    T: number;    // 캔들 종료 시간
    s: string;    // 심볼
    i: string;    // 인터벌
    f: number;    // 첫 거래 ID
    L: number;    // 마지막 거래 ID
    o: string;    // 시가
    c: string;    // 종가
    h: string;    // 고가
    l: string;    // 저가
    v: string;    // 거래량
    n: number;    // 거래 수
    x: boolean;   // 캔들 완료 여부
    q: string;    // 쿼트 거래량
    V: string;    // 테이커 매수 거래량
    Q: string;    // 테이커 매수 쿼트 거래량
  };
}

// 파싱된 실시간 가격 데이터
export interface RealtimePrice {
  symbol: string;
  price: number;
  change24h: number;
  high24h: number;
  low24h: number;
  volume: number;
  updatedAt: Date;
}

// WebSocket 스트림 메시지 (combined stream)
export interface BinanceStreamMessage {
  stream: string;
  data: BinanceTicker | BinanceMiniTicker | BinanceKline;
}
