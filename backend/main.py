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
from auto_trade import (
    NotifyAutoBuyEngine,
    TokenAutoBuyConfig,
    MarketTick,
    MarginSnapshot,
    ExecutionLog,
)

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
    # Prefer encrypted credentials if present
    stored_creds = credential_store.get_mstock_credentials()
    mstock = MStockClient()
    if stored_creds:
        print("Found stored credentials, attempting mStock login...")
        # Override with stored credentials
        mstock.api_key = stored_creds['api_key']
        mstock.client_code = stored_creds['user_id']
        mstock.password = stored_creds['password']
    else:
        print("No stored credentials found. Trying .env variables for mStock login...")
        # MStockClient already loaded .env; if present, login will use them
    login_success = mstock.login()
    # Some SDKs return None/non-boolean on success; rely on client flag
    print(f"mStock Login Status: {login_success}")
    if hasattr(mstock, 'is_connected'):
        print(f"DEBUG: mStock is_connected: {mstock.is_connected}")
    # Do NOT discard the client solely on falsy login_success. Keep for diagnostics.
    if not login_success and not (mstock and getattr(mstock, 'is_connected', False)):
        print("Login failed or SDK missing; keeping client for diagnostics and mock mode")
except Exception as e:
    print(f"Error initializing mStock client: {e}")
    mstock = None

# -----------------------------
# Auto-Buy engine wiring
# -----------------------------
auto_buy_engine = None
auto_buy_selection: list[TokenAutoBuyConfig] = []
auto_buy_log = ExecutionLog()
notifications_buffer: list[dict] = []

def _get_latest_ticks() -> list[MarketTick]:
    """Convert current token snapshot into MarketTick list."""
    ticks: list[MarketTick] = []
    # Use existing live/mock paths to get token data
    # Reuse TOKENS list and mstock connection status
    try:
        if mstock and mstock.is_connected:
            resp, fmt = mstock.get_data_smart(TOKENS)
            # Expect a dict mapping token->fields or list; normalize
            now = asyncio.get_event_loop().time()
            for s in TOKENS:
                ex, sym = s.split(":", 1)
                entry = None
                if isinstance(resp, dict):
                    entry = resp.get(s) or resp.get(sym)
                elif isinstance(resp, list) and resp:
                    # Attempt to find matching symbol in list entries
                    for e in resp:
                        if (e.get("symbol") == sym) or (e.get("token") == sym):
                            entry = e
                            break
                if entry:
                    ticks.append(MarketTick(
                        token=s,
                        ltp=float(entry.get("ltp", entry.get("price", 0.0)) or 0.0),
                        open=float(entry.get("open", 0.0) or 0.0),
                        high=float(entry.get("high", 0.0) or 0.0),
                        low=float(entry.get("low", 0.0) or 0.0),
                        volume=int(entry.get("volume", 0) or 0),
                        timestamp=now,
                    ))
        else:
            # Fallback: synthesize ticks from mock
            now = asyncio.get_event_loop().time()
            import random as _r
            for s in TOKENS:
                base = 100.0 + _r.random() * 50.0
                ticks.append(MarketTick(
                    token=s,
                    ltp=round(base, 2),
                    open=round(base - 1.0, 2),
                    high=round(base + 2.0, 2),
                    low=round(base - 2.0, 2),
                    volume=_r.randint(1000, 500000),
                    timestamp=now,
                ))
    except Exception as e:
        print(f"Auto engine tick fetch error: {e}")
    return ticks

def _get_margin() -> MarginSnapshot:
    # TODO: Integrate with real margin API when available
    return MarginSnapshot(available=100000.0, utilized=0.0)

def _send_notification(kind: str, payload: dict) -> None:
    # Store in buffer for retrieval; never execute trades here
    notifications_buffer.append({"kind": kind, "payload": payload})
    # Cap buffer size
    if len(notifications_buffer) > 500:
        del notifications_buffer[:len(notifications_buffer) - 500]

def _place_buy_order(token: str, qty: int) -> tuple[bool, str]:
    # Safe order placement: use SDK if connected, else simulate
    try:
        if mstock and mstock.is_connected:
            res = mstock.place_order(symbol=token, quantity=qty, order_type='BUY', product='DELIVERY')
            return bool(res.get('success', False)), res.get('order_id', 'UNKNOWN') if isinstance(res, dict) else str(res)
        # Simulate and also track in order history
        oid = random.randint(10000, 99999)
        order_tracker.record_order({
            "order_id": oid,
            "symbol": token,
            "side": "BUY",
            "quantity": qty,
            "timestamp": asyncio.get_event_loop().time(),
        })
        return True, str(oid)
    except Exception as e:
        print(f"Auto-Buy order error: {e}")
        return False, str(e)

async def _auto_engine_loop():
    global auto_buy_engine
    while True:
        try:
            if auto_buy_engine:
                log = auto_buy_engine.step()
                auto_buy_log.entries = log.entries  # keep reference updated
        except Exception as e:
            print(f"Auto engine step error: {e}")
        await asyncio.sleep(2)

@app.on_event("startup")
async def start_auto_engine():
    global auto_buy_engine
    # Initialize engine with empty selection; UI can update via endpoint
    auto_buy_engine = NotifyAutoBuyEngine(
        token_config=auto_buy_selection,
        get_latest_ticks=_get_latest_ticks,
        get_margin=_get_margin,
        send_notification=_send_notification,
        place_buy_order=_place_buy_order,
        log=auto_buy_log,
    )
    asyncio.create_task(_auto_engine_loop())

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

@app.get("/api/notifications")
def get_notifications():
    return {"count": len(notifications_buffer), "items": notifications_buffer[-50:]}

@app.get("/api/autobuy/log")
def get_autobuy_log():
    return {"lines": auto_buy_log.entries[-100:]}

@app.get("/api/autobuy/selection")
def get_autobuy_selection():
    return {"selection": [{"token": c.token, "autobuy": c.autobuy, "quantity": c.quantity} for c in auto_buy_selection]}

@app.post("/api/autobuy/selection")
def set_autobuy_selection(items: list[dict]):
    """Update runtime token selection for auto-buy.
    Expected payload: [{ token: str, autobuy: bool, quantity: int }, ...]
    """
    global auto_buy_selection, auto_buy_engine
    try:
        auto_buy_selection = [TokenAutoBuyConfig(token=i.get("token"), autobuy=bool(i.get("autobuy", False)), quantity=int(i.get("quantity", 1))) for i in items]
        if auto_buy_engine:
            auto_buy_engine.update_token_config(auto_buy_selection)
        return {"status": "updated", "count": len(auto_buy_selection)}
    except Exception as e:
        print(f"Auto-buy selection update error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/tokens", response_model=List[TokenData])
async def get_tokens():
    # Try live feed first if mStock is connected; otherwise fall back to mock
    if mstock and getattr(mstock, 'is_connected', False):
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
            print("DEBUG: Live response empty or unparsable; falling back logic engaged")
        except Exception as e:
            print(f"Live data fetch failed, falling back to mock: {e}")
    
    # Strict debug: avoid silent mock when diagnosing live issues
    import os
    if os.getenv("DEBUG_STRICT_LIVE") == "1":
        raise HTTPException(status_code=503, detail="Live data unavailable; strict debug mode prevents mock fallback")
    
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
    global mstock
    try:
        # Attempt SDK logout if session exists
        if mstock and getattr(mstock, 'is_connected', False):
            try:
                # Some SDKs expose logout/close/end_session methods; call if present
                if hasattr(mstock, 'logout') and callable(getattr(mstock, 'logout')):
                    mstock.logout()
                elif hasattr(mstock, 'close') and callable(getattr(mstock, 'close')):
                    mstock.close()
            except Exception as sdk_err:
                print(f"Warning: SDK logout failed: {sdk_err}")
        credential_store.delete_credentials()
        # Also drop any in-memory mStock client/session so backend switches to mock mode
        mstock = None
        return {"status": "success", "message": "Credentials deleted and session cleared"}
    except Exception as e:
        print(f"Error during logout: {e}")
        return {"status": "error", "message": "Failed to delete credentials"}

@app.post("/api/settings")
async def update_settings(settings: dict):
    print(f"Global settings updated: {settings}")
    # Store settings (in production, save to database)
    global_settings = settings
    return {"status": "saved", "settings": global_settings}

@app.post("/api/execute-trade")
async def execute_trade(trade: dict):
    # Duplicate route removed: this simplified handler shadowed the typed version above.
    # Keep only the typed OrderRequest handler to prevent accidental override.
    raise HTTPException(status_code=409, detail="Duplicate route disabled. Use typed /api/execute-trade endpoint.")

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

