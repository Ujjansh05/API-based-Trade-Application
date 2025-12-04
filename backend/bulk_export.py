"""
After-Market Bulk Data Fetch for Excel Analysis

Usage:
  python bulk_export.py --interval daily --output ../exports/daily.csv
  python bulk_export.py --interval weekly --output ../exports/weekly.csv

Runs only when market is closed (local time 16:00–09:00 by default), unless --force is supplied.
Fetches historical data for 2500+ NSE-listed stocks using mStock SDK when available,
and writes CSV with per-stock OHLC series and basic metadata.
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime, time as dtime
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mstock_client import MStockClient

# Simple market hours (IST): 09:15–15:30. We consider closed if before 09:00 or after 16:00.
MARKET_OPEN = dtime(9, 0)
MARKET_CLOSE = dtime(16, 0)

def market_is_closed_now() -> bool:
    now = datetime.now().time()
    return (now < MARKET_OPEN) or (now > MARKET_CLOSE)

def load_symbol_list() -> List[str]:
    """Load NSE symbols. For now, use TOKENS from main.py or a static list.
    In production, load full NSE universe of 2500+ symbols from a maintained file.
    """
    from main import TOKENS
    return TOKENS  # Replace with full list as needed

def fetch_historical(client: MStockClient, symbol: str, interval: str, points: int = 100) -> List[Dict[str, Any]]:
    """Fetch historical candles for a symbol with given interval and number of points.
    Returns list of dicts with keys: ts, open, high, low, close, volume.
    """
    rows: List[Dict[str, Any]] = []
    try:
        resp = client.get_candles(symbol=symbol, interval=interval, count=points)
        if isinstance(resp, list):
            for c in resp:
                rows.append({
                    'symbol': symbol,
                    'interval': interval,
                    'ts': int(c.get('ts') or c.get('time') or c.get('timestamp', 0)),
                    'open': float(c.get('open')),
                    'high': float(c.get('high')),
                    'low': float(c.get('low')),
                    'close': float(c.get('close')),
                    'volume': int(c.get('volume', 0)),
                })
    except Exception as e:
        print(f"ERROR: historical fetch failed for {symbol} ({interval}): {e}")
    return rows

def write_csv(path: str, rows: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ['symbol', 'interval', 'ts', 'open', 'high', 'low', 'close', 'volume']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"✓ Wrote {len(rows)} rows to {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', choices=['daily', 'weekly'], default='daily')
    parser.add_argument('--output', required=True, help='CSV output path')
    parser.add_argument('--force', action='store_true', help='Run even if market open')
    parser.add_argument('--points', type=int, default=100, help='Number of candles per symbol')
    args = parser.parse_args()

    if not args.force and not market_is_closed_now():
        print('Market appears open. This bulk job is intended for after-market. Use --force to override.')
        sys.exit(1)

    interval_map = {
        'daily': '1d',
        'weekly': '1w',
    }
    sdk_interval = interval_map[args.interval]

    client = MStockClient()
    if not client.login():
        print('WARNING: mStock client login failed; historical fetch may be unavailable.')

    symbols = load_symbol_list()
    all_rows: List[Dict[str, Any]] = []
    failures = 0
    start = time.time()
    for i, sym in enumerate(symbols, 1):
        rows = fetch_historical(client, sym, sdk_interval, points=args.points)
        if rows:
            all_rows.extend(rows)
        else:
            failures += 1
        if i % 100 == 0:
            elapsed = time.time() - start
            print(f"Progress: {i}/{len(symbols)} symbols, rows={len(all_rows)}, failures={failures}, elapsed={elapsed:.1f}s")

    write_csv(args.output, all_rows)
    print(f"Completed. Total symbols: {len(symbols)}, failures: {failures}")

if __name__ == '__main__':
    main()
