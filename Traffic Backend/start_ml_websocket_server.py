#!/usr/bin/env python3
"""
ML-Integrated WebSocket Traffic Data Server
==========================================

This script starts the WebSocket server that fetches real ML traffic data 
from http://localhost:8000/api/v1/ingest/simulation and streams it to the frontend.

Usage:
    python start_ml_websocket_server.py

Requirements:
    pip install fastapi uvicorn httpx
"""

import sys
import subprocess
import importlib.util
import os
import requests
import time

def check_requirements():
    """Check if required packages are installed."""
    required_packages = ['fastapi', 'uvicorn', 'httpx']
    missing_packages = []
    
    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_ml_api():
    """Check if the ML API is accessible."""
    ml_endpoint = "http://localhost:8000/api/v1/ingest/simulation"
    print(f"🔍 Checking ML API at {ml_endpoint}...")
    
    try:
        response = requests.get(ml_endpoint, timeout=5)
        if response.status_code == 200:
            print("✅ ML API is accessible")
            try:
                data = response.json()
                if 'simulation_id' in data and 'direction_metrics' in data:
                    print(f"✅ ML API returning valid data (Simulation: {data.get('simulation_id')})")
                    return True
                else:
                    print("⚠️  ML API accessible but data format may not match expected schema")
                    return True
            except:
                print("⚠️  ML API accessible but returned invalid JSON")
                return True
        else:
            print(f"⚠️  ML API returned status {response.status_code}")
            return True  # Continue anyway, will use fallback data
    except requests.ConnectionError:
        print("❌ Could not connect to ML API")
        print("   Make sure your ML API server is running at http://localhost:8000")
        print("   The WebSocket server will start but use simulated data until ML API is available.")
        return True  # Continue anyway
    except Exception as e:
        print(f"⚠️  Error checking ML API: {e}")
        return True  # Continue anyway

def start_server():
    """Start the ML WebSocket server."""
    print("🚀 Starting ML-Integrated WebSocket Server...")
    print("📡 WebSocket endpoint: ws://localhost:8001/ws/traffic")
    print("🤖 ML API endpoint: http://localhost:8000/api/v1/ingest/simulation")
    print("🌐 Health check: http://localhost:8001/health")
    print("🛠️  Debug ML data: http://localhost:8001/debug/ml-data")
    print("\n⚡ Real-time updates: Every 2 seconds")
    print("🔄 Manual overrides: Supported via WebSocket")
    print("🔍 ML data integration: Auto-fetches from your existing API")
    print("\n" + "="*70)
    
    try:
        # Change to the directory containing the websocket server
        script_dir = os.path.dirname(os.path.abspath(__file__))
        websocket_script = os.path.join(script_dir, "websocket_backend.py")
        
        if not os.path.exists(websocket_script):
            print(f"❌ Error: {websocket_script} not found!")
            print("   Make sure websocket_backend.py exists in the same directory")
            return False
        
        # Start the server using uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "websocket_backend:app",
            "--host", "0.0.0.0",
            "--port", "8001", 
            "--reload",
            "--log-level", "info"
        ]
        
        print(f"🔧 Running command: {' '.join(cmd)}")
        print("\n💡 Tips:")
        print("   - Check http://localhost:8001/health for server status")
        print("   - Use http://localhost:8001/debug/ml-data to see current ML data")
        print("   - Connect frontend to ws://localhost:8001/ws/traffic")
        print("   - Press Ctrl+C to stop the server")
        print("\n" + "="*70)
        
        subprocess.run(cmd, cwd=script_dir)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    print("🚦 ML-Integrated WebSocket Traffic Server")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n🔧 Setup instructions:")
        print("1. Install Python packages: pip install fastapi uvicorn httpx")
        print("2. Run this script again: python start_ml_websocket_server.py")
        sys.exit(1)
    
    # Check ML API accessibility
    if not check_ml_api():
        print("\n❌ ML API check failed")
        response = input("Continue anyway with fallback data? (y/n): ")
        if response.lower() not in ['y', 'yes']:
            sys.exit(1)
    
    # Start server
    if not start_server():
        sys.exit(1)

if __name__ == "__main__":
    main()