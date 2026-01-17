import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useProtocols } from '@/hooks/useDefi';
import { formatTVL, formatChange } from '@/types/defi';

export function ProtocolList() {
  const [showCount, setShowCount] = useState(20);
  const { data: protocols, isLoading, error } = useProtocols(50);

  console.log('[ProtocolList] 렌더링:', protocols?.length, '개 프로토콜');

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Top DeFi Protocols</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="animate-pulse flex items-center gap-4 p-3 rounded-lg bg-muted/50">
                <div className="w-8 h-8 rounded-full bg-muted" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded w-24" />
                  <div className="h-3 bg-muted rounded w-16" />
                </div>
                <div className="h-4 bg-muted rounded w-20" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Top DeFi Protocols</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Failed to load protocols</p>
        </CardContent>
      </Card>
    );
  }

  const displayProtocols = protocols?.slice(0, showCount) || [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Top DeFi Protocols</span>
          <Badge variant="secondary">{protocols?.length || 0} protocols</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* 헤더 */}
          <div className="grid grid-cols-12 gap-2 px-3 py-2 text-xs text-muted-foreground font-medium border-b">
            <div className="col-span-1">#</div>
            <div className="col-span-4">Protocol</div>
            <div className="col-span-2">Category</div>
            <div className="col-span-2 text-right">TVL</div>
            <div className="col-span-1 text-right">1d</div>
            <div className="col-span-2 text-right">Chains</div>
          </div>

          {/* 프로토콜 목록 */}
          {displayProtocols.map((protocol, index) => (
            <div
              key={protocol.id}
              className="grid grid-cols-12 gap-2 px-3 py-2 rounded-lg hover:bg-muted/50 transition-colors items-center"
            >
              {/* 순위 */}
              <div className="col-span-1 text-sm text-muted-foreground">
                {index + 1}
              </div>

              {/* 프로토콜 정보 */}
              <div className="col-span-4 flex items-center gap-2">
                {protocol.logo && (
                  <img
                    src={protocol.logo}
                    alt={protocol.name}
                    className="w-6 h-6 rounded-full"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                )}
                <div className="min-w-0">
                  <p className="font-medium text-sm truncate">{protocol.name}</p>
                  {protocol.symbol && (
                    <p className="text-xs text-muted-foreground">{protocol.symbol}</p>
                  )}
                </div>
              </div>

              {/* 카테고리 */}
              <div className="col-span-2">
                <Badge variant="outline" className="text-xs">
                  {protocol.category}
                </Badge>
              </div>

              {/* TVL */}
              <div className="col-span-2 text-right font-medium text-sm">
                {formatTVL(protocol.tvl)}
              </div>

              {/* 1일 변동 */}
              <div
                className={`col-span-1 text-right text-xs ${
                  (protocol.change_1d ?? 0) >= 0 ? 'text-green-500' : 'text-red-500'
                }`}
              >
                {formatChange(protocol.change_1d)}
              </div>

              {/* 체인 수 */}
              <div className="col-span-2 text-right">
                <Badge variant="secondary" className="text-xs">
                  {protocol.chains.length} chains
                </Badge>
              </div>
            </div>
          ))}
        </div>

        {/* 더보기 버튼 */}
        {protocols && showCount < protocols.length && (
          <div className="mt-4 text-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCount((prev) => prev + 20)}
            >
              Show More ({protocols.length - showCount} remaining)
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
