import { useEffect, useCallback } from 'react';
import { binanceWS } from '@/services/websocket/binanceWS';
import { useRealtimeStore } from '@/store/realtimeStore';
import type { RealtimePrice } from '@/services/websocket/types';

// 실시간 가격 업데이트 훅
export function useRealtimePrices(symbols: string[]) {
  const { prices, isConnected, setPrice, setConnected } = useRealtimeStore();

  useEffect(() => {
    if (symbols.length === 0) {
      console.log('[useRealtimePrices] 심볼 없음, 연결 안함');
      return;
    }

    // 유효한 심볼만 필터링 (주요 토큰)
    const validSymbols = symbols.filter((s) =>
      ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'DOT', 'MATIC', 'LINK', 'UNI', 'SHIB', 'LTC', 'ATOM', 'ARB', 'OP'].includes(s.toUpperCase())
    );

    if (validSymbols.length === 0) {
      console.log('[useRealtimePrices] 유효한 심볼 없음');
      return;
    }

    console.log('[useRealtimePrices] 연결 시작:', validSymbols);

    // 연결 상태 핸들러
    const unsubscribeConnection = binanceWS.onConnectionChange(setConnected);

    // 가격 업데이트 구독
    binanceWS.subscribeAll((price: RealtimePrice) => {
      setPrice(price.symbol, price);
    });

    // WebSocket 연결
    binanceWS.connect(validSymbols);

    return () => {
      console.log('[useRealtimePrices] 연결 해제');
      unsubscribeConnection();
      binanceWS.disconnect();
    };
  }, [symbols.join(','), setPrice, setConnected]);

  return { prices, isConnected };
}

// 단일 심볼 실시간 가격
export function useRealtimePrice(symbol: string | null) {
  const { prices, isConnected } = useRealtimeStore();

  const price = symbol ? prices[symbol.toUpperCase()] : undefined;

  return { price, isConnected };
}

// 연결만 관리 (가격 구독 없이)
export function useRealtimeConnection() {
  const { isConnected, setConnected } = useRealtimeStore();

  const connect = useCallback((symbols: string[]) => {
    const unsubscribe = binanceWS.onConnectionChange(setConnected);
    binanceWS.connect(symbols);
    return unsubscribe;
  }, [setConnected]);

  const disconnect = useCallback(() => {
    binanceWS.disconnect();
  }, []);

  return { isConnected, connect, disconnect };
}
