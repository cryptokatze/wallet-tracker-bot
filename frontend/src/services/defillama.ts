import type { Protocol, ChainTVL, ProtocolDetails } from '@/types/defi';

const DEFILLAMA_API = 'https://api.llama.fi';

// 전체 프로토콜 목록 조회 (TVL 순 정렬)
export async function getProtocols(limit: number = 50): Promise<Protocol[]> {
  console.log(`[DefiLlama] 프로토콜 목록 조회 (상위 ${limit}개)`);

  try {
    const res = await fetch(`${DEFILLAMA_API}/protocols`);

    if (!res.ok) {
      console.error('[DefiLlama] 프로토콜 조회 실패:', res.status);
      throw new Error(`API 에러: ${res.status}`);
    }

    const data = await res.json();

    const protocols: Protocol[] = data
      .filter((p: Protocol) => p.tvl > 0)
      .sort((a: Protocol, b: Protocol) => b.tvl - a.tvl)
      .slice(0, limit)
      .map((p: Protocol) => ({
        id: p.id,
        name: p.name,
        symbol: p.symbol || '',
        category: p.category || 'Unknown',
        chains: p.chains || [],
        tvl: p.tvl,
        change_1d: p.change_1d,
        change_7d: p.change_7d,
        logo: p.logo || '',
        url: p.url,
      }));

    console.log(`[DefiLlama] ${protocols.length}개 프로토콜 조회됨`);
    return protocols;
  } catch (error) {
    console.error('[DefiLlama] 프로토콜 조회 오류:', error);
    throw error;
  }
}

// 체인별 TVL 조회
export async function getChainsTVL(): Promise<ChainTVL[]> {
  console.log('[DefiLlama] 체인 TVL 조회');

  try {
    const res = await fetch(`${DEFILLAMA_API}/v2/chains`);

    if (!res.ok) {
      console.error('[DefiLlama] 체인 TVL 조회 실패:', res.status);
      throw new Error(`API 에러: ${res.status}`);
    }

    const data: ChainTVL[] = await res.json();

    // TVL 순으로 정렬
    const sorted = data
      .filter((c) => c.tvl > 0)
      .sort((a, b) => b.tvl - a.tvl);

    console.log(`[DefiLlama] ${sorted.length}개 체인 TVL 조회됨`);
    return sorted;
  } catch (error) {
    console.error('[DefiLlama] 체인 TVL 조회 오류:', error);
    throw error;
  }
}

// 프로토콜 상세 정보 조회
export async function getProtocolDetails(slug: string): Promise<ProtocolDetails | null> {
  console.log(`[DefiLlama] 프로토콜 상세 조회: ${slug}`);

  try {
    const res = await fetch(`${DEFILLAMA_API}/protocol/${slug}`);

    if (!res.ok) {
      console.error('[DefiLlama] 프로토콜 상세 조회 실패:', res.status);
      return null;
    }

    const data = await res.json();

    // DefiLlama API: tvl은 히스토리 배열, currentChainTvls는 체인별 TVL
    const tvlHistory = Array.isArray(data.tvl)
      ? data.tvl.map((item: { date: number; totalLiquidityUSD: number }) => ({
          date: item.date,
          totalLiquidityUSD: item.totalLiquidityUSD,
        }))
      : [];

    const details: ProtocolDetails = {
      id: data.id,
      name: data.name,
      symbol: data.symbol || '',
      description: data.description,
      tvl: data.currentChainTvls?.total || (Array.isArray(data.tvl) ? data.tvl[data.tvl.length - 1]?.totalLiquidityUSD : data.tvl) || 0,
      chainTvls: data.currentChainTvls || data.chainTvls || {},
      tvlHistory,
    };

    console.log(`[DefiLlama] 프로토콜 상세 조회 완료: ${details.name}`);
    return details;
  } catch (error) {
    console.error('[DefiLlama] 프로토콜 상세 조회 오류:', error);
    return null;
  }
}

// 특정 카테고리 프로토콜 조회
export async function getProtocolsByCategory(
  category: string,
  limit: number = 20
): Promise<Protocol[]> {
  console.log(`[DefiLlama] 카테고리별 프로토콜 조회: ${category}`);

  try {
    const allProtocols = await getProtocols(200);

    const filtered = allProtocols
      .filter((p) => p.category.toLowerCase() === category.toLowerCase())
      .slice(0, limit);

    console.log(`[DefiLlama] ${category} 카테고리: ${filtered.length}개`);
    return filtered;
  } catch (error) {
    console.error('[DefiLlama] 카테고리 조회 오류:', error);
    throw error;
  }
}

// 전체 DeFi TVL 조회
export async function getTotalTVL(): Promise<number> {
  console.log('[DefiLlama] 전체 TVL 조회');

  try {
    const chains = await getChainsTVL();
    const total = chains.reduce((sum, chain) => sum + chain.tvl, 0);

    console.log(`[DefiLlama] 전체 TVL: $${(total / 1e9).toFixed(2)}B`);
    return total;
  } catch (error) {
    console.error('[DefiLlama] 전체 TVL 조회 오류:', error);
    throw error;
  }
}
