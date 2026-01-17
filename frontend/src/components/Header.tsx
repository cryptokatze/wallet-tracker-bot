import { useState } from 'react';
import { Search, RefreshCw, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { usePortfolioStore } from '@/store/portfolioStore';

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
}

export function Header({ onRefresh, isLoading }: HeaderProps) {
  const { walletAddress, setWalletAddress, clearAll } = usePortfolioStore();
  const [inputValue, setInputValue] = useState(walletAddress);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (trimmed && trimmed.length >= 40) {
      console.log('[Header] 지갑 주소 검색:', trimmed);
      setWalletAddress(trimmed);
    }
  };

  const handleClear = () => {
    setInputValue('');
    clearAll();
  };

  return (
    <header className="sticky top-0 z-50 bg-card border-b border-border shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center gap-4">
          {/* 로고 */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <span className="text-white font-bold text-sm">P</span>
            </div>
            <span className="font-semibold text-lg hidden sm:block">Portfolio</span>
          </div>

          {/* 검색바 */}
          <form onSubmit={handleSubmit} className="flex-1 max-w-2xl">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="지갑 주소 입력 (0x...)"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className="pl-10 pr-10 h-10 bg-secondary border-0 rounded-full text-sm"
              />
              {inputValue && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </form>

          {/* 새로고침 버튼 */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onRefresh}
            disabled={isLoading || !walletAddress}
            className="shrink-0"
          >
            <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>
    </header>
  );
}
