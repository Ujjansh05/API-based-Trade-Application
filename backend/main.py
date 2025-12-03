from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import random
import asyncio

from .models import TokenData, StrategyUpdate, OrderRequest
from .mstock_client import MStockClient
from .credential_store import credential_store

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
    """Save mStock credentials securely to encrypted local database"""
    api_key = credentials.get('apiKey')
    user_id = credentials.get('userId')
    password = credentials.get('password')
    
    if api_key and user_id and password:
        try:
            # Save to encrypted database
            credential_store.save_mstock_credentials(api_key, user_id, password)
            return {"status": "success", "message": "Credentials saved securely"}
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return {"status": "error", "message": "Failed to save credentials"}
    else:
        return {"status": "error", "message": "Missing required credentials"}

@app.get("/api/credentials/check")
async def check_credentials():
    """Check if credentials are already saved"""
    exists = credential_store.credentials_exist()
    return {"exists": exists}

@app.get("/api/credentials")
async def get_credentials():
    """Retrieve saved credentials (for backend use only)"""
    creds = credential_store.get_mstock_credentials()
    if creds:
        return {"status": "success", "credentials": creds}
    else:
        return {"status": "error", "message": "No credentials found"}

@app.delete("/api/credentials")
async def delete_credentials():
    """Delete saved credentials (logout/reset)"""
    credential_store.delete_credentials()
    return {"status": "success", "message": "Credentials deleted"}

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

