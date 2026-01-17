import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Token, Chain, ChainAsset, ManualAsset } from '@/types';
import { DEFAULT_CHAINS } from '@/types';

interface PortfolioState {
  // 지갑 주소
  walletAddress: string;
  // 활성화된 체인들
  activeChains: Chain[];
  // 체인별 토큰 데이터
  chainTokens: Record<Chain, Token[]>;
  // 로딩 상태
  isLoading: boolean;
  loadingChains: Chain[];
  // 에러 상태
  errors: Record<Chain, string | null>;
  // 수동 자산
  manualAssets: ManualAsset[];
  // 마지막 업데이트
  lastUpdated: Date | null;

  // 액션
  setWalletAddress: (address: string) => void;
  setActiveChains: (chains: Chain[]) => void;
  setChainTokens: (chain: Chain, tokens: Token[]) => void;
  setLoading: (loading: boolean) => void;
  addLoadingChain: (chain: Chain) => void;
  removeLoadingChain: (chain: Chain) => void;
  setError: (chain: Chain, error: string | null) => void;
  clearAll: () => void;

  // 수동 자산 관리
  addManualAsset: (asset: Omit<ManualAsset, 'id' | 'valueUsd'>) => void;
  removeManualAsset: (id: string) => void;

  // 계산된 값
  getTotalValue: () => number;
  getChainAssets: () => ChainAsset[];
  getAllTokens: () => Token[];
}

const initialChainTokens: Record<Chain, Token[]> = {
  ethereum: [],
  bsc: [],
  polygon: [],
  arbitrum: [],
  optimism: [],
  avalanche: [],
  base: [],
};

const initialErrors: Record<Chain, string | null> = {
  ethereum: null,
  bsc: null,
  polygon: null,
  arbitrum: null,
  optimism: null,
  avalanche: null,
  base: null,
};

export const usePortfolioStore = create<PortfolioState>()(
  persist(
    (set, get) => ({
      walletAddress: '',
      activeChains: DEFAULT_CHAINS,
      chainTokens: { ...initialChainTokens },
      isLoading: false,
      loadingChains: [],
      errors: { ...initialErrors },
      manualAssets: [],
      lastUpdated: null,

      setWalletAddress: (address) => {
        console.log('[Store] 지갑 주소 설정:', address);
        set({
          walletAddress: address,
          chainTokens: { ...initialChainTokens },
          errors: { ...initialErrors },
        });
      },

      setActiveChains: (chains) => {
        console.log('[Store] 활성 체인 설정:', chains);
        set({ activeChains: chains });
      },

      setChainTokens: (chain, tokens) => {
        console.log(`[Store] ${chain} 토큰 설정:`, tokens.length);
        set((state) => ({
          chainTokens: { ...state.chainTokens, [chain]: tokens },
          lastUpdated: new Date(),
        }));
      },

      setLoading: (loading) => set({ isLoading: loading }),

      addLoadingChain: (chain) => {
        set((state) => ({
          loadingChains: [...state.loadingChains, chain],
        }));
      },

      removeLoadingChain: (chain) => {
        set((state) => ({
          loadingChains: state.loadingChains.filter((c) => c !== chain),
        }));
      },

      setError: (chain, error) => {
        set((state) => ({
          errors: { ...state.errors, [chain]: error },
        }));
      },

      clearAll: () => {
        console.log('[Store] 모든 데이터 초기화');
        set({
          walletAddress: '',
          chainTokens: { ...initialChainTokens },
          errors: { ...initialErrors },
          lastUpdated: null,
        });
      },

      addManualAsset: (asset) => {
        const id = `manual-${Date.now()}`;
        const valueUsd = asset.amount * asset.priceUsd;
        const newAsset: ManualAsset = { id, ...asset, valueUsd };

        set((state) => ({
          manualAssets: [...state.manualAssets, newAsset],
        }));
        console.log('[Store] 수동 자산 추가:', newAsset);
      },

      removeManualAsset: (id) => {
        set((state) => ({
          manualAssets: state.manualAssets.filter((a) => a.id !== id),
        }));
        console.log('[Store] 수동 자산 삭제:', id);
      },

      getTotalValue: () => {
        const state = get();
        const chainValue = Object.values(state.chainTokens)
          .flat()
          .reduce((sum, token) => sum + token.valueUsd, 0);
        const manualValue = state.manualAssets.reduce((sum, a) => sum + a.valueUsd, 0);
        return chainValue + manualValue;
      },

      getChainAssets: () => {
        const state = get();
        const totalValue = state.getTotalValue();

        return state.activeChains
          .map((chain) => {
            const tokens = state.chainTokens[chain] || [];
            const chainValue = tokens.reduce((sum, t) => sum + t.valueUsd, 0);
            return {
              chain,
              totalValueUsd: chainValue,
              tokens,
              percentage: totalValue > 0 ? (chainValue / totalValue) * 100 : 0,
            };
          })
          .filter((ca) => ca.totalValueUsd > 0)
          .sort((a, b) => b.totalValueUsd - a.totalValueUsd);
      },

      getAllTokens: () => {
        const state = get();
        return Object.values(state.chainTokens)
          .flat()
          .sort((a, b) => b.valueUsd - a.valueUsd);
      },
    }),
    {
      name: 'crypto-portfolio-v2',
      partialize: (state) => ({
        walletAddress: state.walletAddress,
        activeChains: state.activeChains,
        manualAssets: state.manualAssets,
      }),
    }
  )
);
