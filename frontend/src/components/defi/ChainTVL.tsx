import ReactApexChart from 'react-apexcharts';
import type { ApexOptions } from 'apexcharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useChainsTVL } from '@/hooks/useDefi';
import { formatTVL } from '@/types/defi';

// 체인별 색상 매핑
const CHAIN_COLORS: Record<string, string> = {
  Ethereum: '#627EEA',
  BSC: '#F0B90B',
  Polygon: '#8247E5',
  Arbitrum: '#28A0F0',
  Optimism: '#FF0420',
  Avalanche: '#E84142',
  Base: '#0052FF',
  Solana: '#9945FF',
  Tron: '#FF0000',
  Sui: '#4DA2FF',
  Aptos: '#00CBC6',
  zkSync: '#8C8DFC',
};

function getChainColor(chainName: string): string {
  return CHAIN_COLORS[chainName] || '#6b7280';
}

export function ChainTVL() {
  const { data: chains, isLoading, error } = useChainsTVL();

  console.log('[ChainTVL] 렌더링:', chains?.length, '개 체인');

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Chain TVL Distribution</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[300px]">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (error || !chains) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Chain TVL Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Failed to load chain data</p>
        </CardContent>
      </Card>
    );
  }

  // 상위 10개 체인
  const topChains = chains.slice(0, 10);
  const totalTVL = chains.reduce((sum, c) => sum + c.tvl, 0);

  const series = topChains.map((c) => c.tvl);
  const labels = topChains.map((c) => c.name);
  const colors = topChains.map((c) => getChainColor(c.name));

  const options: ApexOptions = {
    chart: {
      type: 'donut',
      fontFamily: 'inherit',
    },
    labels,
    colors,
    legend: {
      position: 'right',
      fontSize: '12px',
    },
    plotOptions: {
      pie: {
        donut: {
          size: '55%',
          labels: {
            show: true,
            name: {
              show: true,
              fontSize: '12px',
            },
            value: {
              show: true,
              fontSize: '14px',
              fontWeight: 600,
              formatter: (val: string) => formatTVL(parseFloat(val)),
            },
            total: {
              show: true,
              label: 'Total TVL',
              fontSize: '11px',
              formatter: () => formatTVL(totalTVL),
            },
          },
        },
      },
    },
    dataLabels: {
      enabled: false,
    },
    tooltip: {
      y: {
        formatter: (val: number) => formatTVL(val),
      },
    },
    stroke: {
      width: 2,
      colors: ['var(--background)'],
    },
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Chain TVL Distribution</span>
          <Badge variant="secondary">{formatTVL(totalTVL)}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ReactApexChart
          options={options}
          series={series}
          type="donut"
          height={300}
        />

        {/* 체인별 TVL 목록 */}
        <div className="mt-4 space-y-2">
          {topChains.slice(0, 5).map((chain) => (
            <div
              key={chain.name}
              className="flex items-center justify-between text-sm"
            >
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getChainColor(chain.name) }}
                />
                <span>{chain.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-medium">{formatTVL(chain.tvl)}</span>
                <span className="text-muted-foreground text-xs w-12 text-right">
                  {((chain.tvl / totalTVL) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
