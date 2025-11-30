import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class TurningCandleSignal:
    symbol: str
    timeframe: str
    signal: str  # "BUY" / "SELL" / "NONE"
    reason: str


def compute_turning_candle(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Placeholder turning-candle logic.
    Assumes df has columns: date, open, high, low, close, volume
    Returns (signal, reason)
    
    BUY when last candle is green and previous is red (simple example).
    SELL when last candle is red and previous is green.
    """
    if df is None or len(df) < 2:
        return ("NONE", "Insufficient candles")
    last = df.iloc[-1]
    prev = df.iloc[-2]

    last_green = last['close'] > last['open']
    prev_red = prev['close'] < prev['open']

    last_red = last['close'] < last['open']
    prev_green = prev['close'] > prev['open']

    if last_green and prev_red:
        return ("BUY", "Turning candle Red→Green")
    if last_red and prev_green:
        return ("SELL", "Turning candle Green→Red")
    return ("NONE", "No turning pattern")


def price_jump_signal(df: pd.DataFrame, threshold_pct: float = 0.5) -> Tuple[str, str]:
    """
    Live candle price jump logic based on last bar.
    threshold_pct: percentage jump vs previous close.
    """
    if df is None or len(df) < 2:
        return ("NONE", "Insufficient candles")
    last = df.iloc[-1]
    prev = df.iloc[-2]
    pct = (last['close'] - prev['close']) / prev['close'] * 100.0
    if pct >= threshold_pct:
        return ("BUY", f"Price jump +{pct:.2f}%")
    if pct <= -threshold_pct:
        return ("SELL", f"Price drop {pct:.2f}%")
    return ("NONE", f"Change {pct:.2f}% below threshold")

