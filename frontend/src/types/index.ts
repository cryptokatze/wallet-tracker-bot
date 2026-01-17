// 지원하는 체인 목록
export type Chain = 'ethereum' | 'bsc' | 'polygon' | 'arbitrum' | 'optimism' | 'avalanche' | 'base';

export const CHAIN_INFO: Record<Chain, {
  name: string;
  symbol: string;
  color: string;
  decimals: number;
  icon: string;
}> = {
  ethereum: {
    name: 'Ethereum',
    symbol: 'ETH',
    color: '#627EEA',
    decimals: 18,
    icon: '⟠'
  },
  bsc: {
    name: 'BNB Chain',
    symbol: 'BNB',
    color: '#F0B90B',
    decimals: 18,
    icon: '⬡'
  },
  polygon: {
    name: 'Polygon',
    symbol: 'MATIC',
    color: '#8247E5',
    decimals: 18,
    icon: '⬡'
  },
  arbitrum: {
    name: 'Arbitrum',
    symbol: 'ETH',
    color: '#28A0F0',
    decimals: 18,
    icon: '◆'
  },
  optimism: {
    name: 'Optimism',
    symbol: 'ETH',
    color: '#FF0420',
    decimals: 18,
    icon: '⭕'
  },
  avalanche: {
    name: 'Avalanche',
    symbol: 'AVAX',
    color: '#E84142',
    decimals: 18,
    icon: '🔺'
  },
  base: {
    name: 'Base',
    symbol: 'ETH',
    color: '#0052FF',
    decimals: 18,
    icon: '🔵'
  },
};

// 기본 활성화된 체인
export const DEFAULT_CHAINS: Chain[] = ['ethereum', 'bsc', 'polygon', 'arbitrum', 'optimism', 'base'];

// 토큰 정보
export interface Token {
  symbol: string;
  name: string;
  address: string; // 컨트랙트 주소 또는 'native'
  chain: Chain;
  decimals: number;
  balance: string; // 원시 잔액
  formattedBalance: number; // 사람이 읽을 수 있는 잔액
  priceUsd: number;
  valueUsd: number;
  logoUrl?: string;
  priceChange24h?: number; // 24시간 변동률
  isNative?: boolean;
  isVerified?: boolean;
}

// 체인별 자산 요약
export interface ChainAsset {
  chain: Chain;
  totalValueUsd: number;
  tokens: Token[];
  percentage: number;
}

// 포트폴리오 데이터
export interface Portfolio {
  address: string;
  totalValueUsd: number;
  chainAssets: ChainAsset[];
  allTokens: Token[];
  lastUpdated: Date;
}

// 수동 입력 자산
export interface ManualAsset {
  id: string;
  symbol: string;
  name: string;
  amount: number;
  priceUsd: number;
  valueUsd: number;
  logoUrl?: string;
  note?: string; // 거래소 이름 등 메모
}

// CoinGecko 코인 검색 결과
export interface CoinSearchResult {
  id: string;
  name: string;
  symbol: string;
  thumb: string;
  large: string;
}

// 숫자 포맷팅 유틸
export function formatNumber(num: number, decimals = 2): string {
  if (num >= 1e9) return `$${(num / 1e9).toFixed(decimals)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(decimals)}M`;
  if (num >= 1e3) return `$${(num / 1e3).toFixed(decimals)}K`;
  return `$${num.toFixed(decimals)}`;
}

export function formatTokenAmount(amount: number): string {
  if (amount >= 1e9) return `${(amount / 1e9).toFixed(2)}B`;
  if (amount >= 1e6) return `${(amount / 1e6).toFixed(2)}M`;
  if (amount >= 1e3) return `${(amount / 1e3).toFixed(2)}K`;
  if (amount >= 1) return amount.toFixed(2);
  if (amount >= 0.0001) return amount.toFixed(4);
  return '<0.0001';
}

export function formatPercent(percent: number | undefined): string {
  if (percent === undefined || percent === null) return '';
  const sign = percent >= 0 ? '+' : '';
  return `${sign}${percent.toFixed(2)}%`;
}
