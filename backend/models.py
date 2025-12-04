from pydantic import BaseModel
from typing import List, Optional

class StrategyConfig(BaseModel):
    mode: str  # 'AUTO' | 'NOTIFY'
    quantity: int
    stopLoss: float
    target: float
    trailingStop: bool

class StrategyUpdate(BaseModel):
    id: str
    active: bool
    config: StrategyConfig

class TokenData(BaseModel):
    symbol: str
    ltp: float
    change: float
    open: float
    high: float
    low: float
    volume: int
    signal: str  # 'BUY' | 'SELL' | 'NONE'
    strategy: str
    prev_close: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None
    market_cap: Optional[float] = None

class Candle(BaseModel):
    ts: int  # epoch millis
    open: float
    high: float
    low: float
    close: float
    volume: int

class CandleResponse(BaseModel):
    symbol: str
    interval: str  # e.g., '1m','5m','15m'
    count: int
    candles: List[Candle]

class OrderRequest(BaseModel):
    symbol: str
    quantity: int
    order_type: str  # 'BUY' | 'SELL'
    strategy: str  # Which strategy triggered this
    price: float = 0.0  # Current price for logging
