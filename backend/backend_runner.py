"""
Backend Runner - Entry point for packaged backend executable
This allows the backend to run without command-line arguments
"""
import sys
import os

# Add the current directory to Python path for imports to work
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

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

