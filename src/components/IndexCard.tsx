interface IndexCardProps {
  label: string;
  symbol: string;
  value: number | null;
  unit: string;
  change1d: number | null;
  comingSoonText: string;
  changeLabelText: string;
}

export default function IndexCard({
  label,
  symbol,
  value,
  unit,
  change1d,
  comingSoonText,
  changeLabelText,
}: IndexCardProps) {
  const isNull = value === null;
  const isUp = change1d !== null && change1d > 0;
  const isDown = change1d !== null && change1d < 0;
  const decimals = value !== null && Math.abs(value) < 1 ? 4 : 2;
  const changeStr =
    change1d !== null
      ? `${isUp ? '+' : ''}${change1d.toFixed(Math.abs(change1d) < 1 ? 4 : 2)}`
      : '—';

  return (
    <div className="bg-term-card border border-term-border rounded-lg p-5 md:p-7 flex flex-col gap-2 transition-colors hover:border-accent-red/40">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-xs md:text-sm text-term-muted uppercase tracking-wider">{label}</span>
        <span className="font-mono text-base md:text-lg text-accent-red">{symbol}</span>
      </div>
      {isNull ? (
        <div className="font-mono text-4xl md:text-5xl text-term-muted py-2">—</div>
      ) : (
        <div className="font-mono text-4xl md:text-5xl lg:text-6xl font-medium text-term-fg tabular-nums leading-none py-1">
          {value!.toFixed(decimals)}
        </div>
      )}
      <div className="flex items-baseline justify-between mt-auto">
        <span className="font-mono text-xs text-term-muted">{unit}</span>
        {isNull ? (
          <span className="font-mono text-xs text-term-muted italic">{comingSoonText}</span>
        ) : (
          <div className="flex flex-col items-end">
            <span
              className={`font-mono text-sm ${isUp ? 'text-accent-red' : 'text-term-muted'}`}
            >
              {changeStr}
            </span>
            <span className="font-mono text-[10px] text-term-muted">{changeLabelText}</span>
          </div>
        )}
      </div>
    </div>
  );
}
