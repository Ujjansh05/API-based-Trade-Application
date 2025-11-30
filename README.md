# IB Live Trading Automation (Candles + Signals)

This adds a minimal, production-ready Python CLI using `ib_insync` to connect to Interactive Brokers (paper/live), fetch the last 12 candles for a chosen interval, compute two optional signals, and place orders automatically.

## Features
- Connects to IB via TWS/IB Gateway (`paper`: 7497, `live`: 7496)
- Fetches last 12 bars for interval: 1,2,5,10,30,60 minutes
- Displays candles: date, open, high, low, close, volume
- Optional signals:
  - Turning Candle Buy (Red→Green)
  - Live Candle Price Jump (threshold %)
- Places market orders when signals trigger

## Install
Use your Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Ensure TWS or IB Gateway is running and API enabled (Enable DDE/API; read-only OFF if placing trades). For paper trading, use port `7497`; live usually `7496`.

## Run
Examples:

```powershell
# Paper trading, 10-minute candles, turning-candle buy enabled
python main.py --symbols AAPL MSFT --interval 10 --turning-buy --paper

# Add live price jump signal with 0.7% threshold
python main.py --symbols AAPL --interval 10 --live-jump --jump-threshold 0.7 --paper

# Live trading (be careful!)
python main.py --symbols AAPL --interval 10 --turning-buy
```

## Notes
- Symbols: Use IB symbols (e.g., `AAPL`, `MSFT`, `NIFTY` requires correct contract type). This sample uses `Stock` with `SMART`/`USD` by default. For indices, futures, options, adapt `symbol_to_contract` in `main.py`.
- Time interval mapping is limited to intraday minute bars. Day/Week/Month would require different `durationStr` and `barSizeSetting` (extend `BAR_SIZE_MAP`).
- Strategy logic in `strategy.py` is a placeholder; port your exact Excel rules there (columns AR–AW / BU–BZ).
- Orders: Uses market order for simplicity. For production, implement risk checks, position sizing, and `LimitOrder`.

## Structure
- `ib_client.py`: Connection + basic data/order helpers
- `strategy.py`: Turning candle and price jump signals
- `main.py`: CLI orchestrator
- `requirements.txt`: Dependencies

## Extend
- Add CSV/Excel token list loader and loop over many contracts.
- Persist logs and trades.
- Add real-time subscription using `ib.reqRealTimeBars` if needed.
- Add OCA/Bracket orders, stop-loss/take-profit.
