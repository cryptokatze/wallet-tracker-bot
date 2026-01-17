import { formatNumber } from '@/types';
import { Loader2 } from 'lucide-react';

interface TotalValueProps {
  value: number;
  isLoading: boolean;
  lastUpdated: Date | null;
}

export function TotalValue({ value, isLoading, lastUpdated }: TotalValueProps) {
  const formatTime = (date: Date | null) => {
    if (!date) return '';
    return new Date(date).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-card rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-muted-foreground">Total Balance</span>
        {isLoading && (
          <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-4xl font-bold tracking-tight">
          {value > 0 ? formatNumber(value) : '$0.00'}
        </span>
      </div>

      {lastUpdated && (
        <div className="mt-2 text-xs text-muted-foreground">
          Last updated: {formatTime(lastUpdated)}
        </div>
      )}
    </div>
  );
}
