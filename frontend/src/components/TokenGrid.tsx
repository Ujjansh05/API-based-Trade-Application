import React, { useMemo, useState, useEffect } from 'react';
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

export const TokenGrid = () => {
    const [rowData, setRowData] = useState<TokenData[]>([]);

    // Poll for data
    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch('http://127.0.0.1:8000/api/tokens');
                const data = await res.json();
                setRowData(data);
            } catch (err) {
                console.error("Failed to fetch token data", err);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 1000);
        return () => clearInterval(interval);
    }, []);

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
