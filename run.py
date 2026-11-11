"""
run.py
Starts the Uvicorn server for the FastAPI application on 0.0.0.0:8000
so it is accessible from your laptop and mobile phone over local Wi-Fi.
"""
import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    print(f"Starting BiztelAI Copilot Server on http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)