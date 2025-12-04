import React, { useEffect, useRef, useState } from 'react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

type Point = { time: string; ltp: number }

type Props = {
  symbol: string
  maxCandles?: number
  refreshMs?: number
  backendUrl?: string // e.g., http://127.0.0.1:8000
}

export default function CandlestickChart({ symbol, maxCandles = 30, refreshMs = 3000, backendUrl = 'http://127.0.0.1:8000' }: Props) {
  const [series, setSeries] = useState<Point[]>([])
  const timerRef = useRef<number | null>(null)

  // Fetch snapshot from backend and append as a candle for the selected symbol
  const fetchSnapshot = async () => {
    try {
      const res = await fetch(`${backendUrl}/api/tokens`)
      const json = await res.json()
      const item = (json as any[]).find((x) => x.symbol === symbol)
      if (!item) return
      const now = new Date()
      const time = now.toLocaleTimeString()
      const point: Point = { time, ltp: Number(item.ltp) }
      setSeries((prev) => {
        const next = [...prev, point]
        if (next.length > maxCandles) next.shift()
        return next
      })
    } catch (e) {
      // ignore network errors for now
    }
  }

  useEffect(() => {
    fetchSnapshot()
    timerRef.current = window.setInterval(fetchSnapshot, refreshMs)
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, backendUrl, refreshMs])

  const data = series.map((s) => ({ ...s }))

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#222" />
          <XAxis dataKey="time" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v: any, n: any) => [v, n]} />
          <Line type="monotone" dataKey="ltp" stroke="#8b5cf6" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
