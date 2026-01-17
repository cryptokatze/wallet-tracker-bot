import { Wallet, Search } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4">
      <div className="w-20 h-20 rounded-full bg-secondary flex items-center justify-center mb-6">
        <Wallet className="w-10 h-10 text-muted-foreground" />
      </div>

      <h2 className="text-xl font-semibold mb-2">지갑 주소를 입력하세요</h2>
      <p className="text-muted-foreground text-center max-w-md mb-6">
        EVM 지갑 주소를 입력하면 여러 체인의 토큰 잔액을 한눈에 확인할 수 있습니다.
      </p>

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Search className="w-4 h-4" />
        <span>상단 검색창에 0x... 주소 입력</span>
      </div>

      {/* 지원 체인 */}
      <div className="mt-8 flex flex-wrap justify-center gap-2">
        {['Ethereum', 'BNB Chain', 'Polygon', 'Arbitrum', 'Optimism', 'Base'].map((chain) => (
          <span
            key={chain}
            className="px-3 py-1 bg-secondary rounded-full text-xs text-muted-foreground"
          >
            {chain}
          </span>
        ))}
      </div>
    </div>
  );
}
