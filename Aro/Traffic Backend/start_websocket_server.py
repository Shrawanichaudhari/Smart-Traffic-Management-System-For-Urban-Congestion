#!/usr/bin/env python3
"""
WebSocket Traffic Data Server Startup Script
===========================================

This script starts the WebSocket server for real-time traffic data streaming.

Usage:
    python start_websocket_server.py

Requirements:
    pip install fastapi uvicorn websockets
"""

import sys
import subprocess
import importlib.util
import os

def check_requirements():
    """Check if required packages are installed."""
    required_packages = ['fastapi', 'uvicorn', 'websockets']
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

def start_server():
    """Start the WebSocket server."""
    print("🚀 Starting WebSocket Traffic Data Server...")
    print("📡 Server will be available at: ws://localhost:8001/ws/traffic")
    print("🌐 Health check endpoint: http://localhost:8001/health")
    print("📚 API docs: http://localhost:8001/docs")
    print("\n⚡ Real-time updates: Every 1 second")
    print("🔄 Manual overrides: Supported via WebSocket messages")
    print("\n" + "="*60)
    
    try:
        # Change to the directory containing the websocket server
        script_dir = os.path.dirname(os.path.abspath(__file__))
        websocket_script = os.path.join(script_dir, "websocket_backend.py")
        
        if not os.path.exists(websocket_script):
            print(f"❌ Error: {websocket_script} not found!")
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
        subprocess.run(cmd, cwd=script_dir)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    print("🚦 WebSocket Traffic Data Server")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\n🔧 Setup instructions:")
        print("1. Install Python packages: pip install fastapi uvicorn websockets")
        print("2. Run this script again: python start_websocket_server.py")
        sys.exit(1)
    
    # Start server
    if not start_server():
        sys.exit(1)

if __name__ == "__main__":
    main()