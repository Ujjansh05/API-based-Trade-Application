import os
import asyncio
import random
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    # Enable live mode only when API key is present and connection is up
    if os.getenv("MSTOCK_API_KEY") and mstock and getattr(mstock, "is_connected", False):
        live_enabled = True
    else:
        print("Live mStock disabled: missing API key or not connected; mock data will be used")
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
live_enabled = False  # Gate live calls to avoid noisy auth failures when API key/IP not ready

def _get_latest_ticks() -> list[MarketTick]:
    """Convert current token snapshot into MarketTick list."""
    ticks: list[MarketTick] = []
    try:
        if live_enabled and mstock and mstock.is_connected:
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
            print("Live data disabled or not connected; returning empty tick list (no mock)")
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
        "mode": "live" if (mstock and mstock.is_connected and live_enabled) else "offline"
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
    if not (live_enabled and mstock and getattr(mstock, 'is_connected', False)):
        raise HTTPException(status_code=503, detail="Live data unavailable (connection or API key missing)")

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
        raise HTTPException(status_code=502, detail="Live data response empty or unparsable")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Live data fetch failed: {e}")

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
        raise HTTPException(status_code=503, detail="Live candles unavailable (connection or data incomplete)")

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

