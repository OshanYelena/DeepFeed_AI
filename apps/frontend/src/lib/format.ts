const UNITS: [number, string][] = [
  [60, "S"],
  [60, "M"],
  [24, "H"],
  [7, "D"],
  [4.345, "W"],
  [12, "MO"],
  [Infinity, "Y"],
];

/** Compact relative age like "2H", "9H", "3D", "2W" — matches the design's terse timestamps. */
export function shortAge(dateStr: string | null): string {
  if (!dateStr) return "—";
  let diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 0) diff = 0;
  for (const [size, label] of UNITS) {
    if (diff < size || label === "Y") {
      const value = Math.max(1, Math.round(diff));
      return label === "S" ? "NOW" : `${value}${label}`;
    }
    diff /= size;
  }
  return "—";
}

export function scorePct(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}
