"use client";

import { useCallback, useRef } from "react";

/** Draggable 0–1 weight bar with a knob, matching the design's interest-weight control. */
export function WeightSlider({ value, onChange, gradient = true }: { value: number; onChange: (v: number) => void; gradient?: boolean }) {
  const trackRef = useRef<HTMLDivElement>(null);

  const setFromClientX = useCallback(
    (clientX: number) => {
      const track = trackRef.current;
      if (!track) return;
      const rect = track.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      onChange(Math.round(ratio * 20) / 20); // snap to 0.05 steps
    },
    [onChange]
  );

  const handlePointerDown = (e: React.PointerEvent) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    setFromClientX(e.clientX);
  };
  const handlePointerMove = (e: React.PointerEvent) => {
    if (e.buttons !== 1) return;
    setFromClientX(e.clientX);
  };

  const pct = `${Math.max(0, Math.min(1, value)) * 100}%`;

  return (
    <div
      ref={trackRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      className="relative flex-1 h-1 rounded-full bg-surface-hover cursor-pointer touch-none"
    >
      <div
        className="absolute left-0 top-0 bottom-0 rounded-full"
        style={{ width: pct, background: gradient ? "linear-gradient(90deg,#3b82f6,#d946ef)" : "#7c5cf6" }}
      />
      <div
        className="absolute top-1/2 w-4 h-4 rounded-full bg-white shadow"
        style={{ left: pct, transform: "translate(-50%, -50%)" }}
      />
    </div>
  );
}
