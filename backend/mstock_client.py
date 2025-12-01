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
