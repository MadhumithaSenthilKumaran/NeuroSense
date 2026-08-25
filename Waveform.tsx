import React, { useEffect, useRef } from "react";

type WaveformProps = {
  points: number[];
  /** optional extra Tailwind classes for the container */
  className?: string;
};

export default function Waveform({ points, className = "" }: WaveformProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.max(1, window.devicePixelRatio || 1);

    const resizeAndDraw = () => {
      const rect = container.getBoundingClientRect();
      const cssWidth = Math.max(1, Math.floor(rect.width));
      const cssHeight = Math.max(1, Math.floor(rect.height));

      // Set CSS size (so layout stays responsive) and backing store size for crisp rendering
      canvas.style.width = `${cssWidth}px`;
      canvas.style.height = `${cssHeight}px`;
      canvas.width = Math.floor(cssWidth * dpr);
      canvas.height = Math.floor(cssHeight * dpr);

      // Scale drawing operations to device pixels
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      draw();
    };

    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;

      // Clear
      ctx.clearRect(0, 0, w, h);

      if (!points || points.length === 0) return;

      // Determine min/max so points can be arbitrary numeric range
      let min = Infinity;
      let max = -Infinity;
      for (let i = 0; i < points.length; i++) {
        const v = points[i];
        if (v < min) min = v;
        if (v > max) max = v;
      }
      if (min === max) {
        // avoid divide-by-zero when flat line
        min = min - 1;
        max = max + 1;
      }
      const range = max - min;

      // Waveform drawing parameters
      const centerY = h / 2;
      const amplitude = (h / 2) * 0.95; // small padding

      ctx.lineWidth = 1.5;
      ctx.lineCap = "round";
      ctx.strokeStyle = "#60A5FA"; // Tailwind blue-400
      ctx.beginPath();

      for (let i = 0; i < points.length; i++) {
        const t = points.length === 1 ? 0 : i / (points.length - 1);
        const x = t * w;
        const normalized = (points[i] - min) / range; // 0..1
        const value = (normalized - 0.5) * 2; // -1..1 centered
        const y = centerY - value * amplitude;

        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }

      ctx.stroke();

      // Optionally draw a subtle center line
      ctx.strokeStyle = "rgba(0,0,0,0.06)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, centerY + 0.5);
      ctx.lineTo(w, centerY + 0.5);
      ctx.stroke();
    };

    // Use ResizeObserver to respond to container size changes
    const ro = new ResizeObserver(() => resizeAndDraw());
    ro.observe(container);

    // Also redraw on points change or window resize
    window.addEventListener("resize", resizeAndDraw);

    // Initial draw
    resizeAndDraw();

    return () => {
      ro.disconnect();
      window.removeEventListener("resize", resizeAndDraw);
    };
  }, [points]);

  return (
    <div
      ref={containerRef}
      className={`w-full h-24 bg-transparent overflow-hidden ${className}`.trim()}
      // container is sized via Tailwind; make it changeable by passing className
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
}
