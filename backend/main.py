from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import random
import asyncio

from .models import TokenData, StrategyUpdate, OrderRequest

app = FastAPI(title="Antigravity Trader API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Data Store
TOKENS = [
    "NSE:INFY", "NSE:RELIANCE", "NSE:TATASTEEL", "NFO:NIFTY14AUG25C24600"
]

@app.get("/")
def read_root():
    return {"status": "online", "service": "Antigravity Trader"}

@app.get("/api/tokens", response_model=List[TokenData])
async def get_tokens():
    # Simulate live data
    data = []
    for symbol in TOKENS:
        data.append(TokenData(
            symbol=symbol,
            ltp=random.uniform(100, 3000),
            change=random.uniform(-2, 2),
            open=1000.0,
            high=1010.0,
            low=990.0,
            volume=random.randint(1000, 100000),
            signal=random.choice(["BUY", "SELL", "NONE"]),
            strategy=random.choice(["Turning Candle", "Price Jump", "-"])
        ))
    return data

@app.post("/api/config")
async def update_config(update: StrategyUpdate):
    print(f"Received config update for {update.id}: {update.active}")
    return {"status": "updated", "id": update.id}

@app.post("/api/orders")
async def place_order(order: OrderRequest):
    print(f"Placing order: {order}")
    return {"status": "placed", "orderId": random.randint(10000, 99999)}
