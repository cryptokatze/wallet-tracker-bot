import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { TokenCard } from './TokenCard';
import type { Token, Chain } from '@/types';

interface TokenGridProps {
  tokens: Token[];
  selectedChain: Chain | null;
  isLoading: boolean;
  onTokenClick?: (token: Token) => void;
}

export function TokenGrid({ tokens, selectedChain, isLoading, onTokenClick }: TokenGridProps) {
  const [showAll, setShowAll] = useState(false);

  // 선택된 체인 필터링
  const filteredTokens = selectedChain
    ? tokens.filter((t) => t.chain === selectedChain)
    : tokens;

  // 표시할 토큰 수 제한
  const displayLimit = 30;
  const displayTokens = showAll ? filteredTokens : filteredTokens.slice(0, displayLimit);
  const hasMore = filteredTokens.length > displayLimit;

  if (isLoading) {
    return (
      <div className="token-grid">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="bg-card rounded-xl p-4 shadow-sm animate-pulse-soft">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-secondary" />
              <div className="flex-1">
                <div className="h-4 w-16 bg-secondary rounded mb-1" />
                <div className="h-3 w-24 bg-secondary rounded" />
              </div>
            </div>
            <div className="h-6 w-20 bg-secondary rounded mb-2" />
            <div className="h-3 w-full bg-secondary rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (filteredTokens.length === 0) {
    return (
      <div className="bg-card rounded-xl p-8 text-center shadow-sm">
        <div className="text-muted-foreground">
          {selectedChain ? '이 체인에 보유한 토큰이 없습니다' : '보유한 토큰이 없습니다'}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-muted-foreground">
          Wallet ({filteredTokens.length} tokens)
        </h3>
      </div>

      <div className="token-grid">
        {displayTokens.map((token) => (
          <TokenCard
            key={`${token.chain}-${token.address}`}
            token={token}
            onClick={onTokenClick ? () => onTokenClick(token) : undefined}
          />
        ))}
      </div>

      {/* 더보기 버튼 */}
      {hasMore && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="inline-flex items-center gap-1 px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            {showAll ? (
              <>
                <ChevronUp className="w-4 h-4" />
                접기
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                더보기 ({filteredTokens.length - displayLimit}개)
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
