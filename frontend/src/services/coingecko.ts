import type { CoinSearchResult, Chain } from '@/types';

// CoinGecko API 기본 URL
const COINGECKO_API = 'https://api.coingecko.com/api/v3';

// API 키 (Demo Plan)
const getApiKey = (): string => {
  return import.meta.env.VITE_COINGECKO_API_KEY || '';
};

// 헤더 생성
const getHeaders = (): HeadersInit => {
  const apiKey = getApiKey();
  if (apiKey) {
    return { 'x-cg-demo-api-key': apiKey };
  }
  return {};
};

// Rate limit 관리
let lastRequestTime = 0;
const MIN_REQUEST_INTERVAL = 2000; // 2초 (Demo Plan: 30 calls/min)

async function rateLimitedFetch(url: string): Promise<Response> {
  const now = Date.now();
  const timeSinceLastRequest = now - lastRequestTime;

  if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
    await new Promise((resolve) => setTimeout(resolve, MIN_REQUEST_INTERVAL - timeSinceLastRequest));
  }

  lastRequestTime = Date.now();
  return fetch(url, { headers: getHeaders() });
}

// 코인 검색
export async function searchCoins(query: string): Promise<CoinSearchResult[]> {
  if (!query || query.length < 2) return [];

  console.log(`[CoinGecko] 코인 검색: ${query}`);

  try {
    const res = await rateLimitedFetch(`${COINGECKO_API}/search?query=${encodeURIComponent(query)}`);
    const data = await res.json();

    if (!res.ok) {
      console.error('[CoinGecko] 검색 실패:', data);
      return [];
    }

    const results = (data.coins || []).slice(0, 10).map((coin: CoinSearchResult) => ({
      id: coin.id,
      name: coin.name,
      symbol: coin.symbol,
      thumb: coin.thumb,
      large: coin.large,
    }));

    console.log(`[CoinGecko] 검색 결과:`, results.map((r: CoinSearchResult) => r.symbol));
    return results;
  } catch (error) {
    console.error('[CoinGecko] 검색 오류:', error);
    return [];
  }
}

// 코인 가격 조회 (ID 기반)
export async function getCoinPrices(coinIds: string[]): Promise<Record<string, number>> {
  if (coinIds.length === 0) return {};

  const ids = coinIds.join(',');
  console.log(`[CoinGecko] 가격 조회: ${ids}`);

  try {
    const res = await rateLimitedFetch(
      `${COINGECKO_API}/simple/price?ids=${ids}&vs_currencies=usd`
    );
    const data = await res.json();

    if (!res.ok) {
      console.error('[CoinGecko] 가격 조회 실패:', data);
      return {};
    }

    const prices: Record<string, number> = {};
    for (const id of coinIds) {
      prices[id] = data[id]?.usd || 0;
    }

    console.log(`[CoinGecko] 가격 결과:`, prices);
    return prices;
  } catch (error) {
    console.error('[CoinGecko] 가격 조회 오류:', error);
    return {};
  }
}

// 심볼 -> CoinGecko ID 매핑 (주요 코인)
const SYMBOL_TO_ID: Record<string, string> = {
  BTC: 'bitcoin',
  ETH: 'ethereum',
  SOL: 'solana',
  MATIC: 'matic-network',
  USDT: 'tether',
  USDC: 'usd-coin',
  DAI: 'dai',
  WETH: 'weth',
  WBTC: 'wrapped-bitcoin',
  ARB: 'arbitrum',
  OP: 'optimism',
  LINK: 'chainlink',
  UNI: 'uniswap',
  AAVE: 'aave',
  CRV: 'curve-dao-token',
  LDO: 'lido-dao',
  MKR: 'maker',
  SNX: 'synthetix-network-token',
  COMP: 'compound-governance-token',
  SUSHI: 'sushi',
  YFI: 'yearn-finance',
  PEPE: 'pepe',
  SHIB: 'shiba-inu',
  DOGE: 'dogecoin',
  BONK: 'bonk',
  WIF: 'dogwifcoin',
  JUP: 'jupiter-exchange-solana',
  RAY: 'raydium',
  ORCA: 'orca',
};

// 심볼로 가격 조회
export async function getPricesBySymbols(symbols: string[]): Promise<Record<string, number>> {
  const coinIds: string[] = [];
  const symbolToIdMap: Record<string, string> = {};

  for (const symbol of symbols) {
    const upperSymbol = symbol.toUpperCase();
    const id = SYMBOL_TO_ID[upperSymbol];
    if (id) {
      coinIds.push(id);
      symbolToIdMap[upperSymbol] = id;
    }
  }

  if (coinIds.length === 0) {
    console.log('[CoinGecko] 매핑된 코인 ID 없음');
    return {};
  }

  const prices = await getCoinPrices(coinIds);

  // 심볼 -> 가격 매핑으로 변환
  const result: Record<string, number> = {};
  for (const [symbol, id] of Object.entries(symbolToIdMap)) {
    result[symbol] = prices[id] || 0;
  }

  return result;
}

// 체인별 네이티브 토큰 가격 조회
export async function getNativeTokenPrices(): Promise<Record<Chain, number>> {
  const ids = 'ethereum,matic-network,avalanche-2,binancecoin';
  const prices = await getCoinPrices(ids.split(','));

  return {
    ethereum: prices['ethereum'] || 0,
    bsc: prices['binancecoin'] || 0,
    polygon: prices['matic-network'] || 0,
    arbitrum: prices['ethereum'] || 0,
    optimism: prices['ethereum'] || 0,
    avalanche: prices['avalanche-2'] || 0,
    base: prices['ethereum'] || 0,
  };
}

// 코인 상세 정보 조회
export async function getCoinDetails(coinId: string): Promise<{
  price: number;
  image: string;
  name: string;
  symbol: string;
} | null> {
  console.log(`[CoinGecko] 코인 상세 조회: ${coinId}`);

  try {
    const res = await rateLimitedFetch(
      `${COINGECKO_API}/coins/${coinId}?localization=false&tickers=false&community_data=false&developer_data=false`
    );
    const data = await res.json();

    if (!res.ok) {
      console.error('[CoinGecko] 상세 조회 실패:', data);
      return null;
    }

    return {
      price: data.market_data?.current_price?.usd || 0,
      image: data.image?.small || '',
      name: data.name,
      symbol: data.symbol?.toUpperCase(),
    };
  } catch (error) {
    console.error('[CoinGecko] 상세 조회 오류:', error);
    return null;
  }
}

// OHLC 데이터 타입
export interface OHLCData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

// OHLC 캔들스틱 데이터 조회
export async function getCoinOHLC(
  coinId: string,
  days: 1 | 7 | 14 | 30 = 7
): Promise<OHLCData[]> {
  console.log(`[CoinGecko] OHLC 조회: ${coinId}, ${days}일`);

  try {
    const res = await rateLimitedFetch(
      `${COINGECKO_API}/coins/${coinId}/ohlc?vs_currency=usd&days=${days}`
    );

    if (!res.ok) {
      console.error('[CoinGecko] OHLC 조회 실패:', res.status);
      return [];
    }

    const data = await res.json();
    const ohlc = data.map(([time, open, high, low, close]: number[]) => ({
      time,
      open,
      high,
      low,
      close,
    }));

    console.log(`[CoinGecko] OHLC 결과: ${ohlc.length}개 캔들`);
    return ohlc;
  } catch (error) {
    console.error('[CoinGecko] OHLC 조회 오류:', error);
    return [];
  }
}

// Market Chart 데이터 타입
export interface MarketChartData {
  timestamp: number;
  price: number;
}

// 가격 히스토리 조회 (라인 차트용)
export async function getCoinMarketChart(
  coinId: string,
  days: number = 30
): Promise<MarketChartData[]> {
  console.log(`[CoinGecko] Market Chart 조회: ${coinId}, ${days}일`);

  try {
    const res = await rateLimitedFetch(
      `${COINGECKO_API}/coins/${coinId}/market_chart?vs_currency=usd&days=${days}`
    );

    if (!res.ok) {
      console.error('[CoinGecko] Market Chart 조회 실패:', res.status);
      return [];
    }

    const data = await res.json();
    const prices = data.prices.map(([timestamp, price]: [number, number]) => ({
      timestamp,
      price,
    }));

    console.log(`[CoinGecko] Market Chart 결과: ${prices.length}개 데이터 포인트`);
    return prices;
  } catch (error) {
    console.error('[CoinGecko] Market Chart 조회 오류:', error);
    return [];
  }
}

// 심볼로 CoinGecko ID 찾기
export function getCoingeckoId(symbol: string): string | null {
  const upperSymbol = symbol.toUpperCase();
  return SYMBOL_TO_ID[upperSymbol] || null;
}
