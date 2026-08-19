import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface LambdaChartProps {
  data: { date: string; value: number }[];
  dark?: boolean;
  height?: number;
}

export default function LambdaChart({ data, dark = true, height = 360 }: LambdaChartProps) {
  const gridColor = dark ? '#2A2A2E' : '#E5E1D8';
  const axisColor = dark ? '#6B6862' : '#6B6862';
  const tooltipBg = dark ? '#131316' : '#FFFFFF';
  const tooltipBorder = dark ? '#2A2A2E' : '#E5E1D8';

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis
          dataKey="date"
          stroke={axisColor}
          tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }}
          tickFormatter={(v: string) => v.slice(5)}
        />
        <YAxis
          stroke={axisColor}
          tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }}
          domain={['auto', 'auto']}
        />
        <Tooltip
          contentStyle={{
            background: tooltipBg,
            border: `1px solid ${tooltipBorder}`,
            borderRadius: '4px',
            fontFamily: 'JetBrains Mono',
            fontSize: '12px',
          }}
          labelStyle={{ color: dark ? '#F5F2EA' : '#1A1A18' }}
          itemStyle={{ color: '#C8402A' }}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#C8402A"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
