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

class OrderRequest(BaseModel):
    symbol: str
    action: str  # 'BUY' | 'SELL'
    quantity: int
    orderType: str = "MKT"
