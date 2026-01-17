import ReactApexChart from 'react-apexcharts';
import type { ApexOptions } from 'apexcharts';
import type { OHLCData } from '@/services/coingecko';

interface TokenCandlestickProps {
  data: OHLCData[];
  symbol: string;
  isLoading?: boolean;
}

export function TokenCandlestick({ data, symbol, isLoading }: TokenCandlestickProps) {
  console.log('[TokenCandlestick] 렌더링:', symbol, data.length, '개 캔들');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[350px]">
        <div className="animate-pulse text-muted-foreground">Loading chart...</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[350px]">
        <p className="text-muted-foreground text-sm">No chart data available</p>
      </div>
    );
  }

  const series = [
    {
      data: data.map((d) => ({
        x: new Date(d.time),
        y: [d.open, d.high, d.low, d.close],
      })),
    },
  ];

  const options: ApexOptions = {
    chart: {
      type: 'candlestick',
      height: 350,
      fontFamily: 'inherit',
      toolbar: {
        show: true,
        tools: {
          download: false,
          selection: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true,
        },
      },
      animations: {
        enabled: true,
        speed: 300,
      },
    },
    title: {
      text: `${symbol.toUpperCase()} Price`,
      align: 'left',
      style: {
        fontSize: '14px',
        fontWeight: 600,
      },
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeUTC: false,
        format: 'MM/dd HH:mm',
      },
    },
    yaxis: {
      tooltip: {
        enabled: true,
      },
      labels: {
        formatter: (val: number) => {
          if (val >= 1000) return `$${(val / 1000).toFixed(1)}K`;
          if (val >= 1) return `$${val.toFixed(2)}`;
          return `$${val.toFixed(4)}`;
        },
      },
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#00b894',
          downward: '#e74c3c',
        },
        wick: {
          useFillColor: true,
        },
      },
    },
    tooltip: {
      custom: ({ seriesIndex, dataPointIndex, w }) => {
        const o = w.globals.seriesCandleO[seriesIndex][dataPointIndex];
        const h = w.globals.seriesCandleH[seriesIndex][dataPointIndex];
        const l = w.globals.seriesCandleL[seriesIndex][dataPointIndex];
        const c = w.globals.seriesCandleC[seriesIndex][dataPointIndex];
        const date = new Date(w.globals.seriesX[seriesIndex][dataPointIndex]);

        const formatPrice = (p: number) => {
          if (p >= 1000) return `$${p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
          if (p >= 1) return `$${p.toFixed(2)}`;
          return `$${p.toFixed(6)}`;
        };

        return `
          <div class="p-3 bg-background border rounded-lg shadow-lg text-sm">
            <div class="font-medium mb-2">${date.toLocaleString()}</div>
            <div class="grid grid-cols-2 gap-x-4 gap-y-1">
              <span class="text-muted-foreground">Open:</span>
              <span class="text-right">${formatPrice(o)}</span>
              <span class="text-muted-foreground">High:</span>
              <span class="text-right text-green-500">${formatPrice(h)}</span>
              <span class="text-muted-foreground">Low:</span>
              <span class="text-right text-red-500">${formatPrice(l)}</span>
              <span class="text-muted-foreground">Close:</span>
              <span class="text-right font-medium">${formatPrice(c)}</span>
            </div>
          </div>
        `;
      },
    },
    grid: {
      borderColor: 'var(--border)',
    },
  };

  return (
    <ReactApexChart
      options={options}
      series={series}
      type="candlestick"
      height={350}
    />
  );
}
