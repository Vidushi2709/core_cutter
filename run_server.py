"""
Phase Balancing Controller - Main Entry Point

Run this file to start the backend API server.
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Import and run the app
from backend.app import app
import uvicorn

if __name__ == "__main__":
    print("="*60)
    print("Phase Balancing Controller")
    print("="*60)
    print("\n✓ Backend API: http://localhost:8000")
    print("✓ API Docs: http://localhost:8000/docs")
    print("✓ Dashboard: Open frontend/dashboard.html in browser")
    print("\n[Press Ctrl+C to stop]\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
