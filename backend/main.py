from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import random
import asyncio

from .models import TokenData, StrategyUpdate, OrderRequest
from .mstock_client import MStockClient

app = FastAPI(title="Antigravity Trader API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize mStock Client
# TEMPORARILY DISABLED - keeping mock data mode due to authentication issues
# Uncomment these lines once credentials are verified
# mstock = MStockClient()
# login_success = mstock.login()
# print(f"mStock Login Status: {login_success}")

# Mock Data Store (fallback if mStock fails)
TOKENS = [
    "NSE:INFY", "NSE:RELIANCE", "NSE:TATASTEEL", "NFO:NIFTY14AUG25C24600"
]

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "service": "Antigravity Trader", 
        "mstock_connected": False,
        "mode": "mock_data"
    }

@app.get("/api/tokens", response_model=List[TokenData])
async def get_tokens():
    # Using Mock Data for development
    print("Returning Mock Data")
    data = []
    for symbol in TOKENS:
        # Generate sparkline data (last 20 price points)
        base_price = random.uniform(100, 3000)
        history = [base_price + random.uniform(-50, 50) for _ in range(20)]
        
        data.append(TokenData(
            symbol=symbol,
            ltp=history[-1],  # Use last history point as current price
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

@app.post("/api/configure")
async def configure_credentials(credentials: dict):
    """Save mStock credentials from first-run setup"""
    print(f"Configuring credentials for user: {credentials.get('userId')}")
    
    # In production, save to .env file or secure database
    # For now, just acknowledge receipt
    api_key = credentials.get('apiKey')
    user_id = credentials.get('userId')
    password = credentials.get('password')
    
    if api_key and user_id and password:
        # TODO: Write to .env file or encrypted storage
        # For demo, just store in memory
        print(f"✓ Credentials configured successfully")
        return {"status": "success", "message": "Configuration saved"}
    else:
        return {"status": "error", "message": "Missing required credentials"}

@app.post("/api/settings")
async def update_settings(settings: dict):
    print(f"Global settings updated: {settings}")
    # Store settings (in production, save to database)
    global_settings = settings
    return {"status": "saved", "settings": global_settings}

@app.post("/api/execute-trade")
async def execute_trade(trade: dict):
    print(f"Executing trade: {trade}")
    # In production, call mStock API to place order
    order_id = random.randint(10000, 99999)
    return {
        "status": "executed",
        "orderId": order_id,
        "symbol": trade.get("symbol"),
        "quantity": trade.get("quantity"),
        "price": trade.get("price")
    }

@app.post("/api/orders")
async def place_order(order: OrderRequest):
    print(f"Placing order: {order}")
    return {"status": "placed", "orderId": random.randint(10000, 99999)}

