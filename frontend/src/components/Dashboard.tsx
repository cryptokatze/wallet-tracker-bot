import { useState, useEffect } from 'react';
import { usePortfolioStore } from '@/store/portfolioStore';
import { usePortfolio } from '@/hooks/usePortfolio';
import { useRealtimePrices } from '@/hooks/useRealtimePrice';
import { Header } from './Header';
import { TotalValue } from './TotalValue';
import { ChainSummary } from './ChainSummary';
import { TokenGrid } from './TokenGrid';
import { EmptyState } from './EmptyState';
import { TokenDetailModal } from './TokenDetailModal';
import { ChainPieChart } from './charts/ChainPieChart';
import { ProtocolList } from './defi/ProtocolList';
import { ChainTVL } from './defi/ChainTVL';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import type { Chain, Token } from '@/types';

export function Dashboard() {
  const { walletAddress } = usePortfolioStore();
  const {
    isLoading,
    totalValue,
    chainAssets,
    allTokens,
    lastUpdated,
    refetchAll,
  } = usePortfolio();

  const [selectedChain, setSelectedChain] = useState<Chain | null>(null);
  const [selectedToken, setSelectedToken] = useState<Token | null>(null);
  const [activeTab, setActiveTab] = useState('portfolio');

  // 실시간 가격 연결 (보유 토큰의 심볼)
  const tokenSymbols = allTokens.map((t) => t.symbol);
  const { isConnected } = useRealtimePrices(tokenSymbols);

  const handleRefresh = () => {
    console.log('[Dashboard] 새로고침 요청');
    refetchAll();
  };

  const handleTokenClick = (token: Token) => {
    console.log('[Dashboard] 토큰 클릭:', token.symbol);
    setSelectedToken(token);
  };

  useEffect(() => {
    console.log('[Dashboard] 마운트, 탭:', activeTab);
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-background">
      <Header onRefresh={handleRefresh} isLoading={isLoading} />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {!walletAddress ? (
          <EmptyState />
        ) : (
          <div className="space-y-6">
            {/* 총 자산 + 실시간 연결 상태 */}
            <div className="flex items-start justify-between gap-4">
              <TotalValue
                value={totalValue}
                isLoading={isLoading}
                lastUpdated={lastUpdated}
              />
              {isConnected && (
                <Badge variant="outline" className="text-green-500 border-green-500">
                  <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse" />
                  Live
                </Badge>
              )}
            </div>

            {/* 탭 네비게이션 */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList>
                <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
                <TabsTrigger value="defi">DeFi</TabsTrigger>
              </TabsList>

              {/* Portfolio 탭 */}
              <TabsContent value="portfolio">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* 왼쪽: 체인 요약 + 토큰 그리드 */}
                  <div className="lg:col-span-2 space-y-6">
                    <ChainSummary
                      chainAssets={chainAssets}
                      selectedChain={selectedChain}
                      onSelectChain={setSelectedChain}
                    />
                    <TokenGrid
                      tokens={allTokens}
                      selectedChain={selectedChain}
                      isLoading={isLoading && allTokens.length === 0}
                      onTokenClick={handleTokenClick}
                    />
                  </div>

                  {/* 오른쪽: 파이차트 */}
                  <div>
                    <ChainPieChart
                      chainAssets={chainAssets}
                      isLoading={isLoading}
                    />
                  </div>
                </div>
              </TabsContent>

              {/* DeFi 탭 */}
              <TabsContent value="defi">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* 왼쪽: 프로토콜 목록 */}
                  <div className="lg:col-span-2">
                    <ProtocolList />
                  </div>

                  {/* 오른쪽: 체인 TVL */}
                  <div>
                    <ChainTVL />
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </main>

      {/* 토큰 상세 모달 */}
      <TokenDetailModal
        token={selectedToken}
        open={!!selectedToken}
        onClose={() => setSelectedToken(null)}
      />
    </div>
  );
}
