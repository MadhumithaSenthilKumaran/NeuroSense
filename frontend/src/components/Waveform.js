import { jsx as _jsx } from "react/jsx-runtime";
import { useRef, useEffect } from 'react';
export default function Waveform({ points }) {
    const canvasRef = useRef(null);
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas)
            return;
        const ctx = canvas.getContext('2d');
        if (!ctx)
            return;
        const DPR = window.devicePixelRatio || 1;
        function resize() {
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * DPR;
            canvas.height = rect.height * DPR;
            draw();
        }
        function draw() {
            const w = canvas.width;
            const h = canvas.height;
            ctx.clearRect(0, 0, w, h);
            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(0, 0, w, h);
            if (!points || points.length === 0)
                return;
            ctx.lineWidth = 1.5 * DPR;
            ctx.strokeStyle = '#4f46e5';
            ctx.beginPath();
            const step = w / points.length;
            for (let i = 0; i < points.length; i++) {
                const x = i * step;
                const v = points[i];
                const y = (1 - (v + 1) / 2) * h; // assuming points in [-1,1]
                if (i === 0)
                    ctx.moveTo(x, y);
                else
                    ctx.lineTo(x, y);
            }
            ctx.stroke();
        }
        const ro = new ResizeObserver(resize);
        ro.observe(canvas);
        resize();
        return () => ro.disconnect();
    }, [points]);
    return _jsx("canvas", { ref: canvasRef, className: "w-full h-28 rounded-md" });
}
