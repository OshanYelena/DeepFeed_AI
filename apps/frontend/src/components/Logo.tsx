/**
 * Crops the DeepFeed lockup PNG down to just the "D" glyph, the same way
 * the design mockups do with a scaled background-position trick.
 */
export function Logo({ size = 28 }: { size?: number }) {
  const scale = size / 28;
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.25,
        backgroundImage: "url(/logo.png)",
        backgroundSize: `${76 * scale}px ${76 * scale}px`,
        backgroundPosition: `${-25 * scale}px ${-18 * scale}px`,
        backgroundRepeat: "no-repeat",
        flexShrink: 0,
      }}
    />
  );
}
