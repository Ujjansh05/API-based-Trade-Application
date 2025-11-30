import argparse
import pandas as pd
from typing import List
from ib_client import IBClient
from strategy import compute_turning_candle, price_jump_signal, TurningCandleSignal
from ib_insync import Stock
from excel_loader import read_tokens_and_interval

BAR_SIZE_MAP = {
    1: "1 min",
    2: "2 mins",
    5: "5 mins",
    10: "10 mins",
    30: "30 mins",
    60: "1 hour",
}

DURATION_FOR_12 = {
    "1 min": "720 S",   # 12 * 60s
    "2 mins": "1440 S", # 12 * 120s
    "5 mins": "3600 S", # 12 * 300s
    "10 mins": "7200 S",# 12 * 600s
    "30 mins": "21600 S", # 12 * 1800s
    "1 hour": "43200 S",  # 12 * 3600s
}


def parse_args():
    p = argparse.ArgumentParser(description="IB automation: fetch candles and trade")
    p.add_argument("--symbols", nargs="+", help="List of IB symbols (e.g., AAPL MSFT)")
    p.add_argument("--excel", help="Path to Excel file to read tokens/interval from (Column A tokens, Column X interval)")
    p.add_argument("--exchange", default="SMART", help="Exchange routing, default SMART")
    p.add_argument("--currency", default="USD", help="Currency, default USD")
    p.add_argument("--interval", type=int, choices=[1,2,5,10,30,60], default=10, help="Interval in minutes")
    p.add_argument("--turning-buy", action="store_true", help="Enable Turning Candle Buy (Red→Green)")
    p.add_argument("--live-jump", action="store_true", help="Enable Live Candle Price Jump")
    p.add_argument("--jump-threshold", type=float, default=0.5, help="Price jump threshold percent")
    p.add_argument("--paper", action="store_true", help="Use paper trading port 7497; else 7496")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--client-id", type=int, default=1)
    p.add_argument("--quantity", type=float, default=1, help="Order quantity")
    return p.parse_args()


def symbol_to_contract(symbol: str, exchange: str, currency: str):
    return Stock(symbol, exchange, currency)


def main():
    args = parse_args()
    # Load from Excel if provided
    symbols: List[str] = []
    interval_minutes = args.interval
    if args.excel:
        tokens, maybe_interval = read_tokens_and_interval(args.excel, token_col="A", interval_col="X")
        if tokens:
            symbols = tokens
        if maybe_interval:
            interval_minutes = maybe_interval
    if not symbols:
        if not args.symbols:
            raise SystemExit("No symbols provided. Use --symbols or --excel.")
        symbols = args.symbols

    bar_size = BAR_SIZE_MAP[interval_minutes]
    duration = DURATION_FOR_12[bar_size]

    port = 7497 if args.paper else 7496
    ib = IBClient(host=args.host, port=port, client_id=args.client_id)

    print(f"Connecting to IB at {args.host}:{port} (clientId={args.client_id})...")
    ib.connect()

    for symbol in symbols:
        print(f"\n=== {symbol} | {bar_size} | last 12 candles ===")
        contract = symbol_to_contract(symbol, args.exchange, args.currency)
        df = ib.get_bars(contract, duration=duration, bar_size=bar_size, what_to_show="TRADES", use_rth=True)

        if df is None or df.empty:
            print("No data returned.")
            continue

        # Display last 12 candles
        last12 = df.tail(12)
        print(last12[['date','open','high','low','close','volume']].to_string(index=False))

        # Strategy checks
        action = "NONE"
        reasons: List[str] = []

        if args.turning_buy:
            sig, reason = compute_turning_candle(last12)
            reasons.append(f"Turning: {reason}")
            if sig == "BUY":
                action = "BUY"

        if args.live_jump and action == "NONE":
            sig, reason = price_jump_signal(last12, threshold_pct=args.jump_threshold)
            reasons.append(f"Jump: {reason}")
            if sig in ("BUY", "SELL"):
                action = sig

        print("Signals:", "; ".join(reasons))

        # Place order if any action
        if action != "NONE":
            print(f"Placing {action} market order for {symbol}, qty={args.quantity}")
            trade = ib.place_market_order(contract, action, args.quantity)
            print(f"OrderId={trade.order.orderId} | Status={trade.orderStatus.status}")
        else:
            print("No trade action triggered.")

    ib.disconnect()


if __name__ == "__main__":
    main()
