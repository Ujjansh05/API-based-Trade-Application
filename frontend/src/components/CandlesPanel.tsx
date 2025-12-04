import { useEffect, useState } from 'react';

type Interval = '1m' | '5m' | '15m';

interface Candle {
  ts: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface CandleResponse {
  symbol: string;
  interval: Interval;
  count: number;
  candles: Candle[];
}

export function CandlesPanel({ symbol }: { symbol: string }) {
  const [interval, setInterval] = useState<Interval>('1m');
  const [data, setData] = useState<CandleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchCandles = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `http://127.0.0.1:8000/api/candles?symbol=${encodeURIComponent(symbol)}&interval=${interval}&count=12`;
      const res = await fetch(url);
      if (!res.ok) {
        const body = await res.text();
        throw new Error(`HTTP ${res.status}: ${body}`);
      }
      const json = (await res.json()) as CandleResponse;
      if (json.count !== 12 || !Array.isArray(json.candles) || json.candles.length !== 12) {
        throw new Error('Backend did not return exactly 12 candles');
      }
      setData(json);
    } catch (e: any) {
      setError(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (symbol) fetchCandles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, interval]);

  return (
    <div className="glass-panel rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-semibold text-sm">Candles · {symbol || '-'} · {interval}</h3>
        <div className="flex items-center gap-2">
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value as Interval)}
            className="bg-gray-900 text-white text-xs px-2 py-1 rounded-md border border-white/10"
          >
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
          </select>
          <button onClick={fetchCandles} className="text-xs px-2 py-1 rounded-md bg-blue-600 text-white hover:bg-blue-500">Refresh</button>
        </div>
      </div>

      {loading && <div className="text-xs text-gray-400">Loading 12 candles…</div>}
      {error && (
        <div className="text-xs text-red-400">{error}</div>
      )}
      {data && (
        <div className="overflow-auto border border-white/5 rounded-md">
          <table className="w-full text-xs">
            <thead className="bg-gray-800/40 text-gray-300">
              <tr>
                <th className="text-left px-2 py-1">Time</th>
                <th className="text-right px-2 py-1">Open</th>
                <th className="text-right px-2 py-1">High</th>
                <th className="text-right px-2 py-1">Low</th>
                <th className="text-right px-2 py-1">Close</th>
                <th className="text-right px-2 py-1">Volume</th>
              </tr>
            </thead>
            <tbody>
              {data.candles.map((c, i) => (
                <tr key={i} className="odd:bg-gray-900/20">
                  <td className="px-2 py-1 text-gray-300">{new Date(c.ts).toLocaleTimeString()}</td>
                  <td className="px-2 py-1 text-right text-gray-200">{c.open.toFixed(2)}</td>
                  <td className="px-2 py-1 text-right text-gray-200">{c.high.toFixed(2)}</td>
                  <td className="px-2 py-1 text-right text-gray-200">{c.low.toFixed(2)}</td>
                  <td className="px-2 py-1 text-right text-gray-200">{c.close.toFixed(2)}</td>
                  <td className="px-2 py-1 text-right text-gray-400">{c.volume}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
