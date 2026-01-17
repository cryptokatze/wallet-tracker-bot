import { create } from 'zustand';
import type { RealtimePrice } from '@/services/websocket/types';

interface RealtimeState {
  // 실시간 가격 데이터
  prices: Record<string, RealtimePrice>;

  // 연결 상태
  isConnected: boolean;

  // 마지막 업데이트
  lastUpdate: Date | null;

  // 액션
  setPrice: (symbol: string, price: RealtimePrice) => void;
  setPrices: (prices: Record<string, RealtimePrice>) => void;
  setConnected: (connected: boolean) => void;
  clearPrices: () => void;

  // Getter
  getPrice: (symbol: string) => RealtimePrice | undefined;
}

export const useRealtimeStore = create<RealtimeState>((set, get) => ({
  prices: {},
  isConnected: false,
  lastUpdate: null,

  setPrice: (symbol, price) => {
    set((state) => ({
      prices: { ...state.prices, [symbol.toUpperCase()]: price },
      lastUpdate: new Date(),
    }));
  },

  setPrices: (prices) => {
    set({ prices, lastUpdate: new Date() });
  },

  setConnected: (connected) => {
    console.log('[RealtimeStore] 연결 상태:', connected);
    set({ isConnected: connected });
  },

  clearPrices: () => {
    set({ prices: {}, lastUpdate: null });
  },

  getPrice: (symbol) => {
    return get().prices[symbol.toUpperCase()];
  },
}));
