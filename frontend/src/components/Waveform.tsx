import React, { useRef, useEffect } from 'react'

type Props = { points: number[] }

export default function Waveform({ points }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current as HTMLCanvasElement | null
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const DPR = window.devicePixelRatio || 1
    function resize() {
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width * DPR
      canvas.height = rect.height * DPR
      draw()
    }

    function draw() {
      const w = canvas.width
      const h = canvas.height
      ctx.clearRect(0, 0, w, h)

      const gradient = ctx.createLinearGradient(0, 0, w, 0)
      gradient.addColorStop(0, '#e0e7ff')
      gradient.addColorStop(0.5, '#6366f1')
      gradient.addColorStop(1, '#0f172a')
      ctx.fillStyle = '#f8fafc'
      ctx.fillRect(0, 0, w, h)

      if (!points || points.length === 0) return

      const values = points.map(v => Math.max(0, Math.min(1, Math.abs(v))))
      const step = w / values.length
      const midY = h / 2
      const maxBarHeight = h * 0.76

      for (let i = 0; i < values.length; i++) {
        const x = i * step + 0.5
        const amplitude = values[i]
        const barHeight = Math.max(2, amplitude * maxBarHeight)
        const y = midY - barHeight / 2
        ctx.fillStyle = gradient
        ctx.fillRect(x, y, Math.max(1, step * 0.75), barHeight)
      }
    }

    const ro = new ResizeObserver(resize)
    ro.observe(canvas)
    resize()
    return () => ro.disconnect()
  }, [points])

  return <canvas ref={canvasRef} className="w-full h-28 rounded-md" />
}
