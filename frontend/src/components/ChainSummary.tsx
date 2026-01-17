import { CHAIN_INFO, formatNumber, type ChainAsset, type Chain } from '@/types';

interface ChainSummaryProps {
  chainAssets: ChainAsset[];
  selectedChain: Chain | null;
  onSelectChain: (chain: Chain | null) => void;
}

// 체인 아이콘 URL (실제 아이콘 사용)
const CHAIN_ICONS: Record<Chain, string> = {
  ethereum: 'https://icons.llamao.fi/icons/chains/rsz_ethereum.jpg',
  bsc: 'https://icons.llamao.fi/icons/chains/rsz_binance.jpg',
  polygon: 'https://icons.llamao.fi/icons/chains/rsz_polygon.jpg',
  arbitrum: 'https://icons.llamao.fi/icons/chains/rsz_arbitrum.jpg',
  optimism: 'https://icons.llamao.fi/icons/chains/rsz_optimism.jpg',
  avalanche: 'https://icons.llamao.fi/icons/chains/rsz_avalanche.jpg',
  base: 'https://icons.llamao.fi/icons/chains/rsz_base.jpg',
};

export function ChainSummary({ chainAssets, selectedChain, onSelectChain }: ChainSummaryProps) {
  if (chainAssets.length === 0) return null;

  return (
    <div className="bg-card rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-muted-foreground">Portfolio</h3>
        {selectedChain && (
          <button
            onClick={() => onSelectChain(null)}
            className="text-xs text-primary hover:underline"
          >
            All Chains
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        {chainAssets.map((ca) => {
          const chainInfo = CHAIN_INFO[ca.chain];
          const isSelected = selectedChain === ca.chain;

          return (
            <button
              key={ca.chain}
              onClick={() => onSelectChain(isSelected ? null : ca.chain)}
              className={`
                flex items-center gap-2 px-3 py-2 rounded-lg transition-all
                ${isSelected
                  ? 'bg-primary/10 ring-2 ring-primary'
                  : 'bg-secondary hover:bg-secondary/80'
                }
              `}
            >
              <img
                src={CHAIN_ICONS[ca.chain]}
                alt={chainInfo.name}
                className="w-6 h-6 rounded-full"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${chainInfo.symbol}&background=${chainInfo.color.slice(1)}&color=fff&size=24`;
                }}
              />
              <div className="text-left">
                <div className="text-xs text-muted-foreground">{chainInfo.name}</div>
                <div className="text-sm font-semibold">{formatNumber(ca.totalValueUsd)}</div>
              </div>
              <span className="text-xs text-muted-foreground ml-1">
                {ca.percentage.toFixed(0)}%
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
