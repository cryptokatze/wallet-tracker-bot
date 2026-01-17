import { CHAIN_INFO, formatNumber, formatTokenAmount, type Token } from '@/types';

interface TokenCardProps {
  token: Token;
  onClick?: () => void;
}

export function TokenCard({ token, onClick }: TokenCardProps) {
  const chainInfo = CHAIN_INFO[token.chain];
  const priceChange = token.priceChange24h;
  const isPositive = priceChange !== undefined && priceChange >= 0;

  return (
    <div
      className={`bg-card rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow animate-fade-in ${onClick ? 'cursor-pointer hover:ring-2 hover:ring-primary/20' : ''}`}
      onClick={onClick}
    >
      {/* 토큰 아이콘 + 이름 */}
      <div className="flex items-center gap-3 mb-3">
        {token.logoUrl ? (
          <img
            src={token.logoUrl}
            alt={token.symbol}
            className="w-10 h-10 rounded-full"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
              (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
            }}
          />
        ) : null}
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm ${token.logoUrl ? 'hidden' : ''}`}
          style={{ backgroundColor: chainInfo.color }}
        >
          {token.symbol.slice(0, 2).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm truncate">{token.symbol}</div>
          <div className="text-xs text-muted-foreground truncate">{token.name}</div>
        </div>
      </div>

      {/* 금액 */}
      <div className="space-y-1">
        <div className="text-lg font-bold">
          {formatNumber(token.valueUsd)}
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">
            {formatTokenAmount(token.formattedBalance)} {token.symbol}
          </span>
          {priceChange !== undefined && (
            <span className={isPositive ? 'price-positive' : 'price-negative'}>
              {isPositive ? '+' : ''}{priceChange.toFixed(2)}%
            </span>
          )}
        </div>
      </div>

      {/* 체인 표시 */}
      <div className="mt-3 pt-3 border-t border-border">
        <span
          className={`chain-badge chain-badge-${token.chain}`}
          style={{
            backgroundColor: `${chainInfo.color}15`,
            color: chainInfo.color,
          }}
        >
          {chainInfo.name}
        </span>
      </div>
    </div>
  );
}
