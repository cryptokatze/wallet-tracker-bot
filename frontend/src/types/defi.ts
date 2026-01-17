// DeFi 프로토콜 정보
export interface Protocol {
  id: string;
  name: string;
  symbol: string;
  category: string;
  chains: string[];
  tvl: number;
  change_1d: number | null;
  change_7d: number | null;
  logo: string;
  url?: string;
}

// 체인별 TVL 정보
export interface ChainTVL {
  name: string;
  tvl: number;
  tokenSymbol: string;
  chainId?: number;
}

// 프로토콜 상세 정보 (히스토리 포함)
export interface ProtocolDetails {
  id: string;
  name: string;
  symbol: string;
  description?: string;
  tvl: number;
  chainTvls: Record<string, number>;
  tvlHistory: { date: number; totalLiquidityUSD: number }[];
}

// TVL 숫자 포맷팅
export function formatTVL(tvl: number): string {
  if (tvl >= 1e12) return `$${(tvl / 1e12).toFixed(2)}T`;
  if (tvl >= 1e9) return `$${(tvl / 1e9).toFixed(2)}B`;
  if (tvl >= 1e6) return `$${(tvl / 1e6).toFixed(2)}M`;
  if (tvl >= 1e3) return `$${(tvl / 1e3).toFixed(2)}K`;
  return `$${tvl.toFixed(2)}`;
}

// 변동률 포맷팅
export function formatChange(change: number | null): string {
  if (change === null || change === undefined) return '-';
  const sign = change >= 0 ? '+' : '';
  return `${sign}${change.toFixed(2)}%`;
}
