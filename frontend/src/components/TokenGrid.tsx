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
}

// Track price history for sparklines (stores last 20 prices per symbol)
const priceHistory: { [symbol: string]: number[] } = {};

export const TokenGrid = () => {
    const [rowData, setRowData] = useState<TokenData[]>([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch('http://127.0.0.1:8000/api/tokens');
                const data = await res.json();

                // Update price history for each symbol
                data.forEach((token: TokenData) => {
                    if (!priceHistory[token.symbol]) {
                        priceHistory[token.symbol] = [];
                    }
                    priceHistory[token.symbol].push(token.ltp);
                    // Keep only last 20 data points
                    if (priceHistory[token.symbol].length > 20) {
                        priceHistory[token.symbol].shift();
                    }
                });

                setRowData(data);
            } catch (err) {
                console.error("Failed to fetch token data", err);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 1000);
        return () => clearInterval(interval);
    }, []);

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
        <div className="h-full w-full flex flex-col bg-gray-900">
            <div className="bg-green-600 text-white p-2 font-bold">
                📊 Live Trading Data - {rowData.length} Symbols | Updates every second
            </div>
            <div className="flex-1 overflow-auto">
                <table className="w-full text-white">
                    <thead className="bg-gray-800 sticky top-0">
                        <tr>
                            <th className="px-4 py-2 text-left">Symbol</th>
                            <th className="px-4 py-2 text-center" style={{ width: '140px' }}>Price Trend</th>
                            <th className="px-4 py-2 text-right">LTP</th>
                            <th className="px-4 py-2 text-right">Change %</th>
                            <th className="px-4 py-2 text-right">Volume</th>
                            <th className="px-4 py-2 text-center">Signal</th>
                            <th className="px-4 py-2 text-left">Strategy</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rowData.map((row, idx) => (
                            <tr key={idx} className="border-b border-gray-700 hover:bg-gray-800">
                                <td className="px-4 py-3 font-mono font-bold">{row.symbol}</td>
                                <td className="px-4 py-1" style={{ width: '140px' }}>
                                    <MiniChart symbol={row.symbol} />
                                </td>
                                <td className="px-4 py-3 text-right font-bold text-lg">₹{row.ltp.toFixed(2)}</td>
                                <td className={`px-4 py-3 text-right font-semibold ${row.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {row.change >= 0 ? '+' : ''}{row.change.toFixed(2)}%
                                </td>
                                <td className="px-4 py-3 text-right text-gray-300">{row.volume.toLocaleString()}</td>
                                <td className="px-4 py-3 text-center">
                                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${row.signal === 'BUY' ? 'bg-green-600 text-white' :
                                        row.signal === 'SELL' ? 'bg-red-600 text-white' : 'bg-gray-600 text-gray-300'
                                        }`}>
                                        {row.signal}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-gray-300">{row.strategy}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
