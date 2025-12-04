import os
from dotenv import load_dotenv
# Note: Import might vary based on actual package structure. 
# Assuming 'mStock_TradingApi_A' or similar. 
# If the package name is 'mStock-TradingApi-A', the import is likely 'mStock_TradingApi_A' or just 'mStock'.
# I will use a try-except block to handle potential import naming issues or mock it if not found.

try:
    from tradingapi_a.mconnect import MConnect
except ImportError:
    print("mStock SDK not found. Using Mock Client.")
    MConnect = None

# Load .env from project root (one level up from backend/)
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
print(f"DEBUG: Loading .env from: {env_path}")

class MStockClient:
    def __init__(self):
        self.api_key = os.getenv("MSTOCK_API_KEY")
        self.client_code = os.getenv("MSTOCK_USER_ID")
        self.password = os.getenv("MSTOCK_PASSWORD")
        self.client = None
        self.is_connected = False
        
        # Debug: Log what was loaded
        print(f"DEBUG: API Key present: {bool(self.api_key)}")
        print(f"DEBUG: User ID present: {bool(self.client_code)}")
        print(f"DEBUG: Password present: {bool(self.password)}")

    def login(self):
        if not MConnect:
            print("SDK not installed.")
            return False

        try:
            # Initialize SDK
            self.client = MConnect(api_key=self.api_key)
            
            # Perform Login if credentials exist
            if self.client_code and self.password:
                response = self.client.login(
                    user_id=self.client_code,
                    password=self.password
                )
                print(f"mStock Login Response: {response}")
                self.is_connected = True
                return True
            elif self.api_key:
                print("Warning: Only API Key provided. Live data (LTP) will likely fail.")
                self.is_connected = True # Connected to SDK, but not fully authenticated
                return True
            else:
                print("Missing API Key.")
                return False

        except Exception as e:
            print(f"mStock Login Exception: {e}")
            return False

    def get_data(self, tokens):
        """
        Fetch live data for a list of tokens.
        tokens: List of dicts e.g., [{'exchange': 'NSE', 'token': '22'}]
        """
        if not self.client:
            return {}

        try:
            # Try to fetch LTP
            # Note: get_ltp expects a list of instruments
            response = self.client.get_ltp(tokens)
            return response
        except Exception as e:
            print(f"Error fetching data: {e}")
            return {}

    def _split_symbol(self, s: str):
        try:
            parts = s.split(":", 1)
            if len(parts) == 2:
                return parts[0], parts[1]
            return "NSE", s
        except Exception:
            return "NSE", s

    def get_data_smart(self, symbols):
        """
        Try multiple input formats to fetch LTP to avoid token-format mismatch.
        Returns a tuple: (response, format_used)
        format_used: one of 'exchange_symbol', 'exchange_token', 'plain_strings', 'error'
        """
        if not self.client:
            return {}, "error"

        # Variant A: [{'exchange': 'NSE', 'symbol': 'INFY'}]
        ex_sym = []
        for s in symbols:
            ex, sym = self._split_symbol(s)
            ex_sym.append({"exchange": ex, "symbol": sym})
        try:
            resp = self.client.get_ltp(ex_sym)
            if resp:
                print("DEBUG: Live fetch succeeded with exchange+symbol format")
                return resp, "exchange_symbol"
        except Exception as e:
            print(f"DEBUG: exchange+symbol format failed: {e}")

        # Variant B: [{'exchange': 'NSE', 'token': 'INFY'}] (some SDKs use 'token' key for symbol)
        ex_tok = []
        for s in symbols:
            ex, sym = self._split_symbol(s)
            ex_tok.append({"exchange": ex, "token": sym})
        try:
            resp = self.client.get_ltp(ex_tok)
            if resp:
                print("DEBUG: Live fetch succeeded with exchange+token format")
                return resp, "exchange_token"
        except Exception as e:
            print(f"DEBUG: exchange+token format failed: {e}")

        # Variant C: plain strings ["NSE:INFY", ...]
        try:
            resp = self.client.get_ltp(symbols)
            if resp:
                print("DEBUG: Live fetch succeeded with plain strings format")
                return resp, "plain_strings"
        except Exception as e:
            print(f"DEBUG: plain strings format failed: {e}")

        print("DEBUG: Live fetch returned empty for all formats; falling back")
        return {}, "error"

    def place_order(self, symbol, quantity, order_type='BUY', product='DELIVERY'):
        """
        Place an order through mStock API
        
        Args:
            symbol: Trading symbol e.g., 'NSE:INFY' 
            quantity: Number of shares/lots
            order_type: 'BUY' or 'SELL'
            product: 'DELIVERY' or 'INTRADAY'
            
        Returns:
            dict: {'success': bool, 'order_id': str, 'message': str}
        """
        if not self.client or not self.is_connected:
            return {'success': False, 'message': 'Not connected to mStock'}
        
        try:
            # Parse symbol (e.g., 'NSE:INFY' -> exchange='NSE', symbol='INFY')
            parts = symbol.split(':')
            if len(parts) != 2:
                return {'success': False, 'message': 'Invalid symbol format. Use EXCHANGE:SYMBOL'}
            
            exchange, stock_symbol = parts
            
            # Place market order
            response = self.client.place_order(
                exchange=exchange,
                symbol=stock_symbol,
                quantity=quantity,
                order_type='MARKET',  # Always use market orders for simplicity
                side=order_type,  # 'BUY' or 'SELL'
                product=product,
                price=None  # Market order, no price needed
            )
            
            print(f"Order placed: {response}")
            
            # Extract order ID from response
            order_id = response.get('order_id', 'UNKNOWN')
            
            return {
                'success': True,
                'order_id': order_id,
                'message': f'{order_type} order placed for {quantity} {stock_symbol}'
            }
            
        except Exception as e:
            error_msg = f"Order placement failed: {str(e)}"
            print(error_msg)
            return {'success': False, 'message': error_msg}

    def get_candles(self, symbol: str, interval: str, count: int):
        """
        Attempt to fetch historical candles via SDK if available.
        Returns a list of dicts with keys: open, high, low, close, volume, timestamp
        """
        if not self.client:
            return []
        try:
            # Many SDKs expose a historical API like get_historical or get_ohlc
            # Since exact name is unknown, try common variants.
            if hasattr(self.client, 'get_historical'):
                return self.client.get_historical(symbol=symbol, interval=interval, count=count)
            if hasattr(self.client, 'get_ohlc'):
                return self.client.get_ohlc(symbol=symbol, interval=interval, count=count)
        except Exception as e:
            print(f"Error fetching candles: {e}")
        return []
