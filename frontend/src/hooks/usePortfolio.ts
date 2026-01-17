import { useQuery } from '@tanstack/react-query';
import { usePortfolioStore } from '@/store/portfolioStore';
import { getWalletTokenBalances } from '@/services/moralis';
import type { Chain } from '@/types';

export function usePortfolio() {
  const {
    walletAddress,
    activeChains,
    setChainTokens,
    setError,
    addLoadingChain,
    removeLoadingChain,
    getTotalValue,
    getChainAssets,
    getAllTokens,
    loadingChains,
    lastUpdated,
  } = usePortfolioStore();

  // 각 체인별로 쿼리 실행
  const queries = activeChains.map((chain) => {
    return useQuery({
      queryKey: ['portfolio', walletAddress, chain],
      queryFn: async () => {
        console.log(`[usePortfolio] ${chain} 조회 시작`);
        addLoadingChain(chain);
        try {
          const tokens = await getWalletTokenBalances(walletAddress, chain);
          setChainTokens(chain, tokens);
          setError(chain, null);
          return tokens;
        } catch (error) {
          const message = (error as Error).message;
          setError(chain, message);
          console.error(`[usePortfolio] ${chain} 조회 실패:`, message);
          throw error;
        } finally {
          removeLoadingChain(chain);
        }
      },
      enabled: !!walletAddress && walletAddress.length >= 40,
      staleTime: 60 * 1000, // 1분
      retry: 1,
      refetchOnWindowFocus: false,
    });
  });

  const isLoading = loadingChains.length > 0;
  const isAnyError = queries.some((q) => q.isError);

  const refetchAll = async () => {
    console.log('[usePortfolio] 전체 새로고침');
    await Promise.all(queries.map((q) => q.refetch()));
  };

  return {
    isLoading,
    isAnyError,
    loadingChains,
    totalValue: getTotalValue(),
    chainAssets: getChainAssets(),
    allTokens: getAllTokens(),
    lastUpdated,
    refetchAll,
  };
}

// 단일 체인 조회용 훅
export function useChainBalance(chain: Chain) {
  const { walletAddress, setChainTokens } = usePortfolioStore();

  return useQuery({
    queryKey: ['chain-balance', walletAddress, chain],
    queryFn: async () => {
      const tokens = await getWalletTokenBalances(walletAddress, chain);
      setChainTokens(chain, tokens);
      return tokens;
    },
    enabled: !!walletAddress && walletAddress.length >= 40,
    staleTime: 60 * 1000,
    retry: 1,
  });
}
