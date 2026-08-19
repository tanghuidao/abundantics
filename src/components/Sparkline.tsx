import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

interface SparklineProps {
  data: { date: string; value: number }[];
}

export default function Sparkline({ data }: SparklineProps) {
  if (!data || data.length === 0) {
    return <div className="h-[60px] flex items-center justify-center text-term-muted text-xs font-mono">—</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={60}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
        <YAxis domain={['dataMin', 'dataMax']} hide={true} />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#C8402A"
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
