import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { TokenCandlestick } from './charts/TokenCandlestick';
import { useTokenOHLC } from '@/hooks/useTokenChart';
import { formatNumber, formatTokenAmount, formatPercent, type Token } from '@/types';

interface TokenDetailModalProps {
  token: Token | null;
  open: boolean;
  onClose: () => void;
}

type ChartPeriod = 1 | 7 | 14 | 30;

export function TokenDetailModal({ token, open, onClose }: TokenDetailModalProps) {
  const [period, setPeriod] = useState<ChartPeriod>(7);

  const { data: ohlcData, isLoading } = useTokenOHLC(
    token?.symbol || null,
    period
  );

  console.log('[TokenDetailModal] 렌더링:', token?.symbol, 'period:', period);

  if (!token) return null;

  const priceChangeColor = (token.priceChange24h ?? 0) >= 0 ? 'text-green-500' : 'text-red-500';

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            {token.logoUrl && (
              <img
                src={token.logoUrl}
                alt={token.symbol}
                className="w-8 h-8 rounded-full"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            )}
            <div>
              <span className="font-bold">{token.symbol}</span>
              <span className="text-muted-foreground font-normal ml-2">{token.name}</span>
            </div>
          </DialogTitle>
        </DialogHeader>

        {/* 가격 정보 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4 border-y">
          <div>
            <p className="text-xs text-muted-foreground">Price</p>
            <p className="font-semibold">
              ${token.priceUsd >= 1 ? token.priceUsd.toFixed(2) : token.priceUsd.toFixed(6)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">24h Change</p>
            <p className={`font-semibold ${priceChangeColor}`}>
              {formatPercent(token.priceChange24h)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Balance</p>
            <p className="font-semibold">{formatTokenAmount(token.formattedBalance)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Value</p>
            <p className="font-semibold">{formatNumber(token.valueUsd)}</p>
          </div>
        </div>

        {/* 기간 선택 버튼 */}
        <div className="flex gap-2">
          {([1, 7, 14, 30] as ChartPeriod[]).map((p) => (
            <Button
              key={p}
              variant={period === p ? 'default' : 'outline'}
              size="sm"
              onClick={() => setPeriod(p)}
            >
              {p}D
            </Button>
          ))}
        </div>

        {/* 캔들스틱 차트 */}
        <div className="mt-2">
          <TokenCandlestick
            data={ohlcData || []}
            symbol={token.symbol}
            isLoading={isLoading}
          />
        </div>

        {/* 차트 데이터 없을 때 안내 */}
        {!isLoading && (!ohlcData || ohlcData.length === 0) && (
          <p className="text-center text-sm text-muted-foreground mt-2">
            Chart data not available for this token.
            <br />
            Only major tokens are supported.
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}
