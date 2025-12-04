import { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface TokenData {
    symbol: string;
    ltp: number;
    change: number;
    open: number;
    high: number;
    low: number;
    volume: number;
    signal: 'BUY' | 'SELL' | 'NONE';
    strategy: string;
    prev_close?: number;
    week52_high?: number;
    week52_low?: number;
    market_cap?: number;
}

// Track price history for sparklines (stores last 20 prices per symbol)
const priceHistory: { [symbol: string]: number[] } = {};

interface TokenGridProps {
    tokens: TokenData[];
}

export const TokenGrid = ({ tokens }: TokenGridProps) => {
    const [rowData, setRowData] = useState<TokenData[]>([]);

    useEffect(() => {
        // Update price history for each symbol
        tokens.forEach((token: TokenData) => {
            if (!priceHistory[token.symbol]) {
                priceHistory[token.symbol] = [];
            }
            priceHistory[token.symbol].push(token.ltp);
            // Keep only last 20 data points
            if (priceHistory[token.symbol].length > 20) {
                priceHistory[token.symbol].shift();
            }
        });

        setRowData(tokens);
    }, [tokens]);

    // Mini sparkline chart component
    const MiniChart = ({ symbol }: { symbol: string }) => {
        const chartData = useMemo(() => {
            const history = priceHistory[symbol] || [];
            return history.map((price, i) => ({ index: i, price }));
        }, [symbol, priceHistory[symbol]?.length]);

        if (chartData.length < 2) {
            return <div className="text-gray-500 text-xs text-center">...</div>;
        }

        // Color based on trend (green if price went up, red if down)
        const firstPrice = chartData[0].price;
        const lastPrice = chartData[chartData.length - 1].price;
        const color = lastPrice >= firstPrice ? '#4ade80' : '#f87171';

        return (
            <ResponsiveContainer width="100%" height={40}>
                <LineChart data={chartData}>
                    <Line
                        type="monotone"
                        dataKey="price"
                        stroke={color}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        );
    };

    return (
        <div className="h-full w-full flex flex-col">
            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-white/5">
                <div className="flex items-center gap-2">
                    <h2 className="font-semibold text-gray-200">Live Market Data</h2>
                    <span className="px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-400 border border-blue-500/20">
                        {rowData.length} Symbols
                    </span>
                </div>
                <div className="text-xs text-gray-500 font-mono">
                    Updates: 1s
                </div>
            </div>

            <div className="flex-1 overflow-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-gray-400 uppercase bg-gray-900/50 sticky top-0 backdrop-blur-md z-10">
                        <tr>
                            <th className="px-6 py-3 font-medium">Symbol</th>
                            <th className="px-6 py-3 font-medium w-[140px]">Trend (20s)</th>
                            <th className="px-6 py-3 font-medium text-right">LTP</th>
                            <th className="px-6 py-3 font-medium text-right">Change</th>
                            <th className="px-6 py-3 font-medium text-right">Prev Close</th>
                            <th className="px-6 py-3 font-medium text-right">52W H</th>
                            <th className="px-6 py-3 font-medium text-right">52W L</th>
                            <th className="px-6 py-3 font-medium text-right">Mkt Cap</th>
                            <th className="px-6 py-3 font-medium text-right">Volume</th>
                            <th className="px-6 py-3 font-medium text-center">Signal</th>
                            <th className="px-6 py-3 font-medium">Strategy</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {rowData.map((row, idx) => (
                            <tr key={idx} className="hover:bg-white/5 transition-colors group">
                                <td className="px-6 py-3 font-medium text-gray-200 group-hover:text-white transition-colors">
                                    {row.symbol}
                                </td>
                                <td className="px-6 py-1 w-[140px]">
                                    <MiniChart symbol={row.symbol} />
                                </td>
                                <td className="px-6 py-3 text-right font-mono font-medium text-gray-200">
                                    ₹{row.ltp.toFixed(2)}
                                </td>
                                <td className={`px-6 py-3 text-right font-medium ${row.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                    <div className="flex items-center justify-end gap-1">
                                        {row.change >= 0 ? '▲' : '▼'}
                                        {Math.abs(row.change).toFixed(2)}%
                                    </div>
                                </td>
                                <td className="px-6 py-3 text-right text-gray-300 font-mono text-xs">
                                    {row.prev_close != null ? `₹${row.prev_close.toFixed(2)}` : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-300 font-mono text-xs">
                                    {row.week52_high != null ? `₹${row.week52_high.toFixed(2)}` : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-300 font-mono text-xs">
                                    {row.week52_low != null ? `₹${row.week52_low.toFixed(2)}` : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-300 font-mono text-xs">
                                    {row.market_cap != null ? `${Math.round(row.market_cap/1e9)}B` : '-'}
                                </td>
                                <td className="px-6 py-3 text-right text-gray-400 font-mono text-xs">
                                    {row.volume.toLocaleString()}
                                </td>
                                <td className="px-6 py-3 text-center">
                                    {row.signal !== 'NONE' && (
                                        <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider border ${row.signal === 'BUY'
                                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                            }`}>
                                            {row.signal}
                                        </span>
                                    )}
                                    {row.signal === 'NONE' && <span className="text-gray-600">-</span>}
                                </td>
                                <td className="px-6 py-3 text-gray-400 text-xs">
                                    {row.strategy !== '-' ? (
                                        <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                            {row.strategy}
                                        </span>
                                    ) : '-'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
