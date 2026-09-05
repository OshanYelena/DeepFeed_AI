export function ScoreBar({ value, color, width = 56 }: { value: number; color: string; width?: number }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <span className="score-bar inline-block align-middle" style={{ width }}>
      <span className="score-fill block" style={{ width: `${pct}%`, background: color }} />
    </span>
  );
}
