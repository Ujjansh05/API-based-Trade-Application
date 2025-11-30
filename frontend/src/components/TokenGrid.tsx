import { useMemo, useState } from 'react';
import { AgGridReact } from 'ag-grid-react';
import type { ColDef } from 'ag-grid-community';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

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

const MOCK_DATA: TokenData[] = [
    { symbol: 'NSE:INFY', ltp: 1450.5, change: 1.2, open: 1440, high: 1460, low: 1435, volume: 500000, signal: 'BUY', strategy: 'Turning Candle' },
    { symbol: 'NFO:NIFTY14AUG25C24600', ltp: 120.0, change: -5.5, open: 125, high: 130, low: 110, volume: 150000, signal: 'SELL', strategy: 'Price Jump' },
    { symbol: 'NSE:RELIANCE', ltp: 2400.0, change: 0.5, open: 2390, high: 2410, low: 2380, volume: 300000, signal: 'NONE', strategy: '-' },
    { symbol: 'NSE:TATASTEEL', ltp: 110.0, change: 2.1, open: 108, high: 112, low: 107, volume: 1000000, signal: 'BUY', strategy: 'Day Low Double' },
];

export const TokenGrid = () => {
    const [rowData] = useState<TokenData[]>(MOCK_DATA);

    const columnDefs = useMemo<ColDef[]>(() => [
        { field: 'symbol', headerName: 'Token', sortable: true, filter: true, width: 180, pinned: 'left' },
        {
            field: 'ltp',
            headerName: 'LTP',
            sortable: true,
            width: 100,
            cellClass: 'font-mono',
            valueFormatter: (params) => params.value.toFixed(2)
        },
        {
            field: 'change',
            headerName: 'Change %',
            sortable: true,
            width: 110,
            cellRenderer: (params: any) => {
                const val = params.value;
                const color = val > 0 ? 'text-green-500' : val < 0 ? 'text-red-500' : 'text-muted-foreground';
                return (
                    <div className={`flex items-center ${color}`}>
                        {val > 0 ? <ArrowUp size={14} className="mr-1" /> : val < 0 ? <ArrowDown size={14} className="mr-1" /> : <Minus size={14} className="mr-1" />}
                        {Math.abs(val).toFixed(2)}%
                    </div>
                );
            }
        },
        {
            field: 'signal', headerName: 'Signal', width: 100, cellRenderer: (params: any) => {
                const val = params.value;
                if (val === 'BUY') return <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-500 text-xs font-bold">BUY</span>;
                if (val === 'SELL') return <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-500 text-xs font-bold">SELL</span>;
                return <span className="text-muted-foreground">-</span>;
            }
        },
        { field: 'strategy', headerName: 'Strategy', width: 150 },
        { field: 'open', headerName: 'Open', width: 100 },
        { field: 'high', headerName: 'High', width: 100 },
        { field: 'low', headerName: 'Low', width: 100 },
        { field: 'volume', headerName: 'Volume', width: 120, valueFormatter: (params) => params.value.toLocaleString() },
    ], []);

    return (
        <div className="ag-theme-alpine-dark h-full w-full">
            <AgGridReact
                rowData={rowData}
                columnDefs={columnDefs}
                animateRows={true}
                rowSelection="multiple"
                defaultColDef={{
                    resizable: true,
                    sortable: true,
                }}
            />
        </div>
    );
};
