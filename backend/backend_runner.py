"""
Backend Runner - Entry point for packaged backend executable
This allows the backend to run without command-line arguments
"""
import uvicorn
from main import app

if __name__ == "__main__":
    print("Starting Antigravity Trader Backend...")
    print("Server running on http://127.0.0.1:8000")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="info",
        access_log=False  # Disable access logs for cleaner output
    )
