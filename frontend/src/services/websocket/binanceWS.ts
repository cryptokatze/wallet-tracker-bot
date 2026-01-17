import type { BinanceTicker, BinanceStreamMessage, RealtimePrice } from './types';

type PriceHandler = (price: RealtimePrice) => void;
type ConnectionHandler = (connected: boolean) => void;

class BinanceWebSocket {
  private ws: WebSocket | null = null;
  private subscriptions = new Map<string, PriceHandler>();
  private connectionHandlers = new Set<ConnectionHandler>();
  private reconnectAttempts = 0;
  private maxReconnects = 5;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private isManualClose = false;
  private activeSymbols: string[] = [];
  private refCount = 0; // 연결 참조 카운트

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // 연결 상태 변경 리스너 등록
  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    return () => this.connectionHandlers.delete(handler);
  }

  private notifyConnectionChange(connected: boolean) {
    this.connectionHandlers.forEach((handler) => handler(connected));
  }

  // 심볼 목록으로 연결 (참조 카운트 증가)
  connect(symbols: string[]) {
    this.refCount++;
    console.log(`[BinanceWS] 연결 요청 (refCount: ${this.refCount})`);

    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[BinanceWS] 이미 연결됨');
      return;
    }

    this.isManualClose = false;
    this.activeSymbols = symbols;

    // 심볼을 Binance 형식으로 변환 (ETH -> ethusdt@ticker)
    const streams = symbols.map((s) => `${s.toLowerCase()}usdt@ticker`);
    const streamParam = streams.join('/');
    const url = `wss://stream.binance.com:9443/stream?streams=${streamParam}`;

    console.log('[BinanceWS] 연결 시작:', symbols);

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[BinanceWS] 연결됨');
        this.reconnectAttempts = 0;
        this.notifyConnectionChange(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: BinanceStreamMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('[BinanceWS] 메시지 파싱 오류:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[BinanceWS] 에러:', error);
      };

      this.ws.onclose = (event) => {
        console.log('[BinanceWS] 연결 종료:', event.code, event.reason);
        this.notifyConnectionChange(false);

        if (!this.isManualClose && this.refCount > 0) {
          this.attemptReconnect(this.activeSymbols);
        }
      };
    } catch (error) {
      console.error('[BinanceWS] 연결 실패:', error);
    }
  }

  private handleMessage(message: BinanceStreamMessage) {
    const { stream, data } = message;

    // ticker 데이터 처리
    if (stream.endsWith('@ticker')) {
      const ticker = data as BinanceTicker;
      const symbol = ticker.s.replace('USDT', '');

      const price: RealtimePrice = {
        symbol,
        price: parseFloat(ticker.c),
        change24h: parseFloat(ticker.P),
        high24h: parseFloat(ticker.h),
        low24h: parseFloat(ticker.l),
        volume: parseFloat(ticker.v),
        updatedAt: new Date(),
      };

      // 구독자에게 알림
      const handler = this.subscriptions.get(symbol);
      if (handler) {
        handler(price);
      }

      // 전체 구독자에게도 알림 (*)
      const allHandler = this.subscriptions.get('*');
      if (allHandler) {
        allHandler(price);
      }
    }
  }

  private attemptReconnect(symbols: string[]) {
    if (this.reconnectAttempts >= this.maxReconnects) {
      console.log('[BinanceWS] 최대 재연결 시도 횟수 초과');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(3000 * this.reconnectAttempts, 15000);

    console.log(
      `[BinanceWS] ${delay / 1000}초 후 재연결 시도 (${this.reconnectAttempts}/${this.maxReconnects})`
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect(symbols);
    }, delay);
  }

  // 특정 심볼 구독
  subscribe(symbol: string, handler: PriceHandler) {
    console.log('[BinanceWS] 구독:', symbol);
    this.subscriptions.set(symbol.toUpperCase(), handler);
  }

  // 모든 가격 업데이트 구독
  subscribeAll(handler: PriceHandler) {
    console.log('[BinanceWS] 전체 구독');
    this.subscriptions.set('*', handler);
  }

  // 구독 해제
  unsubscribe(symbol: string) {
    console.log('[BinanceWS] 구독 해제:', symbol);
    this.subscriptions.delete(symbol.toUpperCase());
  }

  // 연결 종료 (참조 카운트 감소, 0이면 실제 종료)
  disconnect() {
    this.refCount = Math.max(0, this.refCount - 1);
    console.log(`[BinanceWS] 연결 해제 요청 (refCount: ${this.refCount})`);

    // 아직 사용 중인 컴포넌트가 있으면 연결 유지
    if (this.refCount > 0) {
      console.log('[BinanceWS] 다른 컴포넌트가 사용 중, 연결 유지');
      return;
    }

    console.log('[BinanceWS] 모든 사용 종료, 실제 연결 종료');
    this.isManualClose = true;

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.subscriptions.clear();
    this.activeSymbols = [];
    this.notifyConnectionChange(false);
  }

  // 강제 연결 종료 (디버깅/테스트용)
  forceDisconnect() {
    console.log('[BinanceWS] 강제 연결 종료');
    this.refCount = 0;
    this.disconnect();
  }
}

// 싱글톤 인스턴스
export const binanceWS = new BinanceWebSocket();
