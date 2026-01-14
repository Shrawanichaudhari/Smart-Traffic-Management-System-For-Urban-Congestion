#!/usr/bin/env python3
"""Start the multi-node City WebSocket backend.

WebSocket endpoint:
  ws://localhost:8001/ws/city
HTTP endpoints:
  http://localhost:8001/health
  http://localhost:8001/city/config

Requirements:
  pip install fastapi uvicorn
"""

import os
import subprocess
import sys


def main() -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "city_websocket_backend:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8001",
        "--reload",
        "--log-level",
        "info",
    ]

    print("Starting City WebSocket server...")
    print("WebSocket: ws://localhost:8001/ws/city")
    print("Health:    http://localhost:8001/health")
    print("Config:    http://localhost:8001/city/config")

    subprocess.run(cmd, cwd=script_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
