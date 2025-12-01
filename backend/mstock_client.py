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

load_dotenv()

class MStockClient:
    def __init__(self):
        self.api_key = os.getenv("MSTOCK_API_KEY")
        self.client_code = os.getenv("MSTOCK_USER_ID")
        self.password = os.getenv("MSTOCK_PASSWORD")
        self.client = None
        self.is_connected = False

    def login(self):
        if not MConnect:
            print("SDK not installed.")
            return False

        try:
            # Initialize SDK
            self.client = MConnect(api_key=self.api_key)
            
            # Perform Login
            # SDK signature: login(self, user_id, password)
            if self.client_code and self.password:
                response = self.client.login(
                    user_id=self.client_code,
                    password=self.password
                )
                # Note: SDK might not return a response, or might throw if failed.
                # Assuming success if no error for now, or check response if available.
                print(f"mStock Login Response: {response}")
                self.is_connected = True
                return True
            else:
                print("Missing Client Code or Password for login.")
                return False

        except Exception as e:
            print(f"mStock Login Exception: {e}")
            return False

    def get_quotes(self, instruments):
        """
        Fetch live data for a list of instruments.
        instruments: List of dicts e.g., [{'exchange': 'NSE', 'token': '22'}]
        """
        if not self.is_connected:
            return {}

        try:
            # Hypothetical bulk fetch
            # If SDK supports websocket, we would use that. For now, assuming REST polling.
            response = self.client.get_quotes(instruments)
            return response
        except Exception as e:
            print(f"Error fetching quotes: {e}")
            return {}
