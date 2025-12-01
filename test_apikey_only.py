from tradingapi_a.mconnect import MConnect
import os
from dotenv import load_dotenv

load_dotenv()

# api_key = os.getenv("MSTOCK_API_KEY")
api_key = "dummy_key_for_testing_auth_flow"
if not api_key:
    print("Please set MSTOCK_API_KEY in .env")
    exit(1)

client = MConnect(api_key=api_key)

try:
    # Try to fetch LTP for Nifty 50 (NSE Token 26000 is usually Nifty 50, but let's try a common stock like INFY or just a guess)
    # Assuming standard format: [{'exchange': 'NSE', 'token': '22'}]
    response = client.get_ltp([{'exchange': 'NSE', 'token': '22'}]) 
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
