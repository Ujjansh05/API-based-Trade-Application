from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import random
import asyncio

# Use absolute imports for PyInstaller compatibility
from models import TokenData, StrategyUpdate, OrderRequest, CandleResponse, Candle
from mstock_client import MStockClient
from credential_store import credential_store
from order_tracker import order_tracker

app = FastAPI(title="Antigravity Trader API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize mStock Client with stored credentials
mstock = None
try:
    # Try to get credentials from encrypted database
    stored_creds = credential_store.get_mstock_credentials()
    if stored_creds:
        print("Found stored credentials, attempting mStock login...")
        mstock = MStockClient()
        # Override with stored credentials
        mstock.api_key = stored_creds['api_key']
        mstock.client_code = stored_creds['user_id']
        mstock.password = stored_creds['password']
        login_success = mstock.login()
        print(f"mStock Login Status: {login_success}")
        if not login_success:
            print("Login failed, falling back to mock data")
            mstock = None
    else:
        print("No stored credentials found, using mock data")
except Exception as e:
    print(f"Error initializing mStock client: {e}")
    mstock = None

# Mock Data Store (fallback if mStock fails)
TOKENS = [
    # IT Sector
    "NSE:INFY", "NSE:TCS", "NSE:WIPRO", "NSE:TECHM", "NSE:HCLTECH",
    # Banking & Finance
    "NSE:HDFCBANK", "NSE:ICICIBANK", "NSE:SBIN", "NSE:KOTAKBANK", "NSE:AXISBANK",
    # Energy & Power
    "NSE:RELIANCE", "NSE:ONGC", "NSE:POWERGRID", "NSE:NTPC",
    # Metals & Mining
    "NSE:TATASTEEL", "NSE:HINDALCO", "NSE:VEDL", "NSE:JSWSTEEL",
    # FMCG & Consumer
    "NSE:HINDUNILVR", "NSE:ITC", "NSE:NESTLEIND", "NSE:BRITANNIA",
    # Auto
    "NSE:MARUTI", "NSE:TATAMOTORS", "NSE:M&M", "NSE:BAJAJ-AUTO",
    # Pharma
    "NSE:SUNPHARMA", "NSE:DRREDDY", "NSE:CIPLA", "NSE:DIVISLAB",
    # Index Options (Examples)
    "NFO:NIFTY14AUG25C24600", "NFO:BANKNIFTY14AUG25P50000"
]

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "service": "Antigravity Trader", 
        "mstock_connected": mstock is not None and mstock.is_connected,
        "mode": "live" if (mstock and mstock.is_connected) else "mock_data"
    }

@app.get("/api/tokens", response_model=List[TokenData])
async def get_tokens():
    # Try live feed first if mStock is connected; otherwise fall back to mock
    if mstock and mstock.is_connected:
        try:
            live_response, fmt = mstock.get_data_smart(TOKENS)
            print(f"DEBUG: /api/tokens live format used: {fmt}")
            if isinstance(live_response, dict) and live_response:
                data: List[TokenData] = []
                for s in TOKENS:
                    parts = s.split(":")
                    key_candidates = [s, parts[-1]]
                    payload = {}
                    for k in key_candidates:
                        if k in live_response:
                            payload = live_response.get(k, {})
                            break
                    # Some SDKs return list; handle that too
                    if not payload and isinstance(live_response, list):
                        for item in live_response:
                            if isinstance(item, dict) and (item.get("symbol") == parts[-1] or item.get("token") == parts[-1]):
                                payload = item
                                break
                    ltp = None
                    if isinstance(payload, dict):
                        ltp = payload.get("ltp") or payload.get("price") or payload.get("LTP")
                    if ltp is not None:
                        prev_close_val = None
                        # Prefer previous close from live payload when available
                        for key in ("previousClose", "prevClose", "prev_close", "yesterdayClose"):
                            if isinstance(payload, dict) and payload.get(key) is not None:
                                try:
                                    prev_close_val = float(payload.get(key))
                                except Exception:
                                    pass
                                break
                        change_pct = 0.0
                        if prev_close_val is not None:
                            try:
                                change_pct = round(((float(ltp) - prev_close_val) / prev_close_val) * 100, 2)
                            except Exception:
                                change_pct = 0.0
                        else:
                            # Fallback change based on open if previous close missing
                            change_pct = round(((float(ltp) - float(payload.get("open", ltp))) / float(payload.get("open", ltp))) * 100, 2) if payload.get("open") else 0.0

                        data.append(TokenData(
                            symbol=s,
                            ltp=round(float(ltp), 2),
                            change=change_pct,
                            open=round(float(payload.get("open", ltp)), 2),
                            high=round(float(payload.get("high", ltp)), 2),
                            low=round(float(payload.get("low", ltp)), 2),
                            volume=int(payload.get("volume", 0)),
                            signal="NONE",
                            strategy="-",
                            prev_close=prev_close_val,
                            week52_high=None,
                            week52_low=None,
                            market_cap=None,
                        ))
                if data:
                    print("Returning Live Data")
                    return data
            print("DEBUG: Live response empty or unparsable; falling back to mock")
        except Exception as e:
            print(f"Live data fetch failed, falling back to mock: {e}")
    
    # Fallback to Mock Data (Enhanced with 30+ stocks)
    print("Returning Mock Data")
    
    # Realistic base prices for Indian stocks (approximate current market prices)
    stock_prices = {
        # IT Sector
        "NSE:INFY": 1450, "NSE:TCS": 3800, "NSE:WIPRO": 256, "NSE:TECHM": 1200, "NSE:HCLTECH": 1350,
        # Banking & Finance
        "NSE:HDFCBANK": 1650, "NSE:ICICIBANK": 1100, "NSE:SBIN": 780, "NSE:KOTAKBANK": 1750, "NSE:AXISBANK": 1080,
        # Energy & Power
        "NSE:RELIANCE": 2850, "NSE:ONGC": 280, "NSE:POWERGRID": 310, "NSE:NTPC": 350,
        # Metals & Mining
        "NSE:TATASTEEL": 140, "NSE:HINDALCO": 620, "NSE:VEDL": 450, "NSE:JSWSTEEL": 920,
        # FMCG & Consumer
        "NSE:HINDUNILVR": 2400, "NSE:ITC": 450, "NSE:NESTLEIND": 2200, "NSE:BRITANNIA": 4800,
        # Auto
        "NSE:MARUTI": 12500, "NSE:TATAMOTORS": 780, "NSE:M&M": 2850, "NSE:BAJAJ-AUTO": 9500,
        # Pharma
        "NSE:SUNPHARMA": 1750, "NSE:DRREDDY": 1350, "NSE:CIPLA": 1450, "NSE:DIVISLAB": 5800,
        # Index Options
        "NFO:NIFTY14AUG25C24600": 150, "NFO:BANKNIFTY14AUG25P50000": 280
    }
    
    data = []
    for symbol in TOKENS:
        # Get realistic base price
        base_price = stock_prices.get(symbol, 500)
        
        # Add small random variation (-2% to +2%)
        price_variation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + price_variation)
        
        # Calculate realistic OHLC data
        day_open = base_price * random.uniform(0.98, 1.02)
        day_high = max(current_price, day_open) * random.uniform(1.00, 1.01)
        day_low = min(current_price, day_open) * random.uniform(0.99, 1.00)
        
        # Derive previous close and change percentage (prefer realistic previous close approx)
        prev_close = base_price * random.uniform(0.98, 1.02)
        price_change = ((current_price - prev_close) / prev_close) * 100
        
        # Check if price hit target for notification testing
        signal = "NONE"
        strategy = "-"
        if price_change >= 3.0:
            signal = "BUY"
            strategy = "Price Jump"
        elif price_change <= -3.0:
            signal = "SELL"
            strategy = "Turning Candle"
        elif random.random() < 0.05:  # 5% chance for random signals
            signal = random.choice(["BUY", "SELL"])
            strategy = random.choice(["Price Jump", "Turning Candle", "Day Low Double"])
        
        # Mock metadata for 52-week stats and market cap (placeholder realistic ranges)
        week52_high = base_price * random.uniform(1.15, 1.45)
        week52_low = base_price * random.uniform(0.55, 0.85)
        market_cap = random.uniform(1e11, 2e13)  # in INR

        data.append(TokenData(
            symbol=symbol,
            ltp=round(current_price, 2),
            change=round(price_change, 2),
            open=round(day_open, 2),
            high=round(day_high, 2),
            low=round(day_low, 2),
            volume=random.randint(100000, 10000000),
            signal=signal,
            strategy=strategy,
            prev_close=round(prev_close, 2),
            week52_high=round(week52_high, 2),
            week52_low=round(week52_low, 2),
            market_cap=round(market_cap, 2)
        ))
    return data

@app.get("/api/candles", response_model=CandleResponse)
async def get_candles(symbol: str, interval: str = "1m", count: int = 12):
    """Return exactly 12 candles for the requested interval with validation.
    If live is available, attempt to fetch; otherwise synthesize from mock base price.
    """
    if count != 12:
        raise HTTPException(status_code=400, detail="count must be exactly 12")

    # Basic interval validation
    allowed = {"1m", "5m", "15m"}
    if interval not in allowed:
        raise HTTPException(status_code=400, detail=f"interval must be one of {sorted(list(allowed))}")

    candles: List[Candle] = []
    try:
        if mstock and mstock.is_connected and hasattr(mstock, "get_candles"):
            resp = mstock.get_candles(symbol=symbol, interval=interval, count=count)
            # Expect list of dicts with o/h/l/c/v and timestamp
            if isinstance(resp, list) and len(resp) >= 12:
                resp = resp[-12:]
                for c in resp:
                    candles.append(Candle(
                        ts=int(c.get("ts") or c.get("time") or c.get("timestamp", 0)),
                        open=float(c.get("open")),
                        high=float(c.get("high")),
                        low=float(c.get("low")),
                        close=float(c.get("close")),
                        volume=int(c.get("volume", 0)),
                    ))
    except Exception as e:
        print(f"Live candle fetch failed: {e}")

    if len(candles) != 12:
        # Synthesize 12 candles from mock base
        import time, random
        base = 500.0
        # If symbol in our mock price map, use that
        base = {
            "NSE:INFY": 1450, "NSE:TCS": 3800, "NSE:WIPRO": 256, "NSE:TECHM": 1200, "NSE:HCLTECH": 1350,
        }.get(symbol, base)
        now = int(time.time()*1000)
        step_ms = {"1m": 60_000, "5m": 300_000, "15m": 900_000}[interval]
        candles = []
        price = base
        for i in range(12):
            # small random walk
            drift = random.uniform(-0.01, 0.01)
            o = price
            h = o * (1 + max(drift, 0) * random.uniform(0.2, 1.0))
            l = o * (1 + min(drift, 0) * random.uniform(0.2, 1.0))
            c = o * (1 + drift)
            v = random.randint(10000, 1000000)
            candles.append(Candle(ts=now - (11-i)*step_ms, open=round(o,2), high=round(h,2), low=round(l,2), close=round(c,2), volume=v))
            price = c

    # Final validation
    if len(candles) != 12:
        raise HTTPException(status_code=500, detail="failed to produce exactly 12 candles")

    return CandleResponse(symbol=symbol, interval=interval, count=12, candles=candles)

@app.post("/api/config")
async def update_config(update: StrategyUpdate):
    print(f"Received config update for {update.id}: {update.active}")
    return {"status": "updated", "id": update.id}

@app.post("/api/execute-trade")
async def execute_trade(order: OrderRequest):
    """
    Execute a trade when strategy Auto-Buy is enabled and signal triggers
    
    This endpoint is called from frontend when:
    - User has Auto-Buy enabled on a strategy card
    - That strategy detects a signal (BUY/SELL)
    """
    try:
        # Check daily order limit
        daily_limit = 10  # Default limit
        today_count = order_tracker.get_today_count()
        
        if today_count >= daily_limit:
            return {
                "success": False,
                "message": f"Daily order limit ({daily_limit}) reached. Orders today: {today_count}"
            }
        
        # If mStock is connected, place real order
        if mstock and mstock.is_connected:
            result = mstock.place_order(
                symbol=order.symbol,
                quantity=order.quantity,
                order_type=order.order_type,
                product='INTRADAY'  # Use intraday for now
            )
            
            if result['success']:
                # Log the order
                order_tracker.add_order(
                    order_id=result['order_id'],
                    symbol=order.symbol,
                    quantity=order.quantity,
                    order_type=order.order_type,
                    strategy=order.strategy,
                    price=order.price
                )
                return result
            else:
                return result
        else:
            # Simulated order for testing (when not connected to mStock)
            import uuid
            order_id = f"SIM-{uuid.uuid4().hex[:8]}"
            order_tracker.add_order(
                order_id=order_id,
                symbol=order.symbol,
                quantity=order.quantity,
                order_type=order.order_type,
                strategy=order.strategy,
                price=order.price
            )
            return {
                "success": True,
                "order_id": order_id,
                "message": f"SIMULATED: {order.order_type} {order.quantity} {order.symbol}"
            }
            
    except Exception as e:
        print(f"Trade execution error: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/orders/today")
async def get_today_orders():
    """Get orders placed today"""
    orders = order_tracker.get_today_orders()
    count = order_tracker.get_today_count()
    return {
        "orders": orders,
        "count": count,
        "limit": 10
    }

@app.get("/api/orders/recent")
async def get_recent_orders():
    """Get recent order history"""
    orders = order_tracker.get_recent_orders(limit=50)
    return {"orders": orders}

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

@app.get("/api/live/raw")
async def live_raw():
    """Return raw live response from SDK for debugging token format issues."""
    if mstock and mstock.is_connected:
        try:
            resp, fmt = mstock.get_data_smart(TOKENS)
            return {"format": fmt, "response": resp}
        except Exception as e:
            return {"format": "error", "message": str(e)}
    return {"format": "disconnected", "message": "mStock not connected"}

