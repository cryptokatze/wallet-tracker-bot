import { useQuery } from '@tanstack/react-query';
import { getProtocols, getChainsTVL, getProtocolDetails } from '@/services/defillama';
import type { Protocol, ChainTVL, ProtocolDetails } from '@/types/defi';

// 프로토콜 목록 훅
export function useProtocols(limit: number = 50) {
  return useQuery<Protocol[]>({
    queryKey: ['defi-protocols', limit],
    queryFn: () => getProtocols(limit),
    staleTime: 5 * 60 * 1000, // 5분
    retry: 2,
  });
}

// 체인별 TVL 훅
export function useChainsTVL() {
  return useQuery<ChainTVL[]>({
    queryKey: ['chains-tvl'],
    queryFn: getChainsTVL,
    staleTime: 5 * 60 * 1000, // 5분
    retry: 2,
  });
}

// 프로토콜 상세 훅
export function useProtocolDetails(slug: string | null) {
  return useQuery<ProtocolDetails | null>({
    queryKey: ['protocol-details', slug],
    queryFn: () => getProtocolDetails(slug!),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

// 프로토콜 검색/필터 훅
export function useFilteredProtocols(
  limit: number = 50,
  category?: string,
  chain?: string
) {
  const { data: protocols, ...rest } = useProtocols(limit);

  const filtered = protocols?.filter((p) => {
    if (category && p.category.toLowerCase() !== category.toLowerCase()) {
      return false;
    }
    if (chain && !p.chains.some((c) => c.toLowerCase() === chain.toLowerCase())) {
      return false;
    }
    return true;
  });

  return {
    data: filtered,
    ...rest,
  };
}
