import { useQuery } from '@tanstack/react-query';
import { getCoinOHLC, getCoinMarketChart, getCoingeckoId, type OHLCData, type MarketChartData } from '@/services/coingecko';

// OHLC 데이터 훅 (캔들스틱 차트용)
export function useTokenOHLC(symbol: string | null, days: 1 | 7 | 14 | 30 = 7) {
  const coinId = symbol ? getCoingeckoId(symbol) : null;

  return useQuery<OHLCData[]>({
    queryKey: ['token-ohlc', coinId, days],
    queryFn: async () => {
      if (!coinId) {
        console.log('[useTokenOHLC] CoinGecko ID 없음:', symbol);
        return [];
      }
      return getCoinOHLC(coinId, days);
    },
    enabled: !!coinId,
    staleTime: 5 * 60 * 1000, // 5분
    retry: 1,
  });
}

// Market Chart 훅 (라인 차트용)
export function useTokenMarketChart(symbol: string | null, days: number = 30) {
  const coinId = symbol ? getCoingeckoId(symbol) : null;

  return useQuery<MarketChartData[]>({
    queryKey: ['token-market-chart', coinId, days],
    queryFn: async () => {
      if (!coinId) {
        console.log('[useTokenMarketChart] CoinGecko ID 없음:', symbol);
        return [];
      }
      return getCoinMarketChart(coinId, days);
    },
    enabled: !!coinId,
    staleTime: 5 * 60 * 1000, // 5분
    retry: 1,
  });
}

// CoinGecko ID로 직접 조회하는 버전
export function useTokenOHLCById(coinId: string | null, days: 1 | 7 | 14 | 30 = 7) {
  return useQuery<OHLCData[]>({
    queryKey: ['token-ohlc', coinId, days],
    queryFn: () => getCoinOHLC(coinId!, days),
    enabled: !!coinId,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useTokenMarketChartById(coinId: string | null, days: number = 30) {
  return useQuery<MarketChartData[]>({
    queryKey: ['token-market-chart', coinId, days],
    queryFn: () => getCoinMarketChart(coinId!, days),
    enabled: !!coinId,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
