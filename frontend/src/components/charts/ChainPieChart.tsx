import ReactApexChart from 'react-apexcharts';
import type { ApexOptions } from 'apexcharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CHAIN_INFO, formatNumber, type ChainAsset } from '@/types';

interface ChainPieChartProps {
  chainAssets: ChainAsset[];
  isLoading?: boolean;
}

export function ChainPieChart({ chainAssets, isLoading }: ChainPieChartProps) {
  // 가치가 있는 체인만 필터링
  const validAssets = chainAssets.filter((ca) => ca.totalValueUsd > 0);

  console.log('[ChainPieChart] 렌더링:', validAssets.length, '개 체인');

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Chain Distribution</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[280px]">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (validAssets.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Chain Distribution</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[280px]">
          <p className="text-muted-foreground text-sm">No assets found</p>
        </CardContent>
      </Card>
    );
  }

  const series = validAssets.map((ca) => ca.totalValueUsd);
  const labels = validAssets.map((ca) => CHAIN_INFO[ca.chain].name);
  const colors = validAssets.map((ca) => CHAIN_INFO[ca.chain].color);

  const options: ApexOptions = {
    chart: {
      type: 'donut',
      fontFamily: 'inherit',
      animations: {
        enabled: true,
        speed: 500,
      },
    },
    labels,
    colors,
    legend: {
      position: 'bottom',
      fontSize: '12px',
      markers: {
        size: 8,
      },
      itemMargin: {
        horizontal: 8,
        vertical: 4,
      },
    },
    plotOptions: {
      pie: {
        donut: {
          size: '60%',
          labels: {
            show: true,
            name: {
              show: true,
              fontSize: '14px',
              fontWeight: 600,
            },
            value: {
              show: true,
              fontSize: '18px',
              fontWeight: 700,
              formatter: (val: string) => formatNumber(parseFloat(val)),
            },
            total: {
              show: true,
              label: 'Total',
              fontSize: '12px',
              formatter: (w: { globals: { seriesTotals: number[] } }) => {
                const total = w.globals.seriesTotals.reduce((a: number, b: number) => a + b, 0);
                return formatNumber(total);
              },
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
        formatter: (val: number) => formatNumber(val),
      },
    },
    stroke: {
      width: 2,
      colors: ['var(--background)'],
    },
    responsive: [
      {
        breakpoint: 480,
        options: {
          chart: {
            height: 280,
          },
          legend: {
            position: 'bottom',
          },
        },
      },
    ],
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Chain Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ReactApexChart
          options={options}
          series={series}
          type="donut"
          height={280}
        />
      </CardContent>
    </Card>
  );
}
