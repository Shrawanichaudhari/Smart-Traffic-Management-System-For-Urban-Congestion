#!/usr/bin/env python3
"""
Real-time Data Test Simulator for SIH Traffic Dashboard
Simulates ML model output and posts data to the backend every 2 seconds
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
UPDATE_INTERVAL = 2  # seconds
INTERSECTION_ID = "INT_001"

class TrafficSimulator:
    def __init__(self):
        self.current_cycle = 0
        self.signal_phases = ["north", "south", "east", "west"]  # Simple 4-phase cycle
        self.current_phase = 0
        self.phase_duration = 30  # seconds per phase
        self.phase_timer = self.phase_duration
        
        # Initial lane states
        self.lanes = {
            "n-straight": {
                "direction": "north",
                "type": "straight",
                "current_light": "red",
                "time_remaining": 25,
                "max_time": 30,
                "vehicle_count": 8,
                "avg_speed": 25.5,
                "queue_length": 3
            },
            "s-straight": {
                "direction": "south", 
                "type": "straight",
                "current_light": "red",
                "time_remaining": 35,
                "max_time": 45,
                "vehicle_count": 12,
                "avg_speed": 18.2,
                "queue_length": 5
            },
            "e-straight": {
                "direction": "east",
                "type": "straight",
                "current_light": "red", 
                "time_remaining": 15,
                "max_time": 45,
                "vehicle_count": 15,
                "avg_speed": 12.8,
                "queue_length": 7
            },
            "w-straight": {
                "direction": "west",
                "type": "straight",
                "current_light": "red",
                "time_remaining": 20, 
                "max_time": 45,
                "vehicle_count": 9,
                "avg_speed": 22.1,
                "queue_length": 4
            }
        }
        
        print(f"🚦 Traffic Simulator Initialized")
        print(f"📍 Intersection: {INTERSECTION_ID}")
        print(f"⏱️ Update Interval: {UPDATE_INTERVAL} seconds")
        print(f"🎯 Backend: {BACKEND_URL}")
        print("-" * 60)

    def simulate_ai_decision(self) -> Dict[str, Any]:
        """Simulate AI/ML model making traffic signal decisions"""
        
        # Simple AI logic: prioritize direction with most vehicles
        max_vehicles = 0
        priority_direction = None
        
        for lane_id, lane_data in self.lanes.items():
            if lane_data["vehicle_count"] > max_vehicles:
                max_vehicles = lane_data["vehicle_count"]
                priority_direction = lane_data["direction"]
        
        # Update signal states based on AI decision
        for lane_id, lane_data in self.lanes.items():
            if lane_data["direction"] == priority_direction:
                lane_data["current_light"] = "green"
                lane_data["time_remaining"] = lane_data["max_time"]
            else:
                lane_data["current_light"] = "red"
                lane_data["time_remaining"] = random.randint(15, 45)
            
            # Simulate vehicle flow changes
            if lane_data["current_light"] == "green":
                # Vehicles moving, reduce count
                lane_data["vehicle_count"] = max(0, lane_data["vehicle_count"] - random.randint(1, 3))
                lane_data["avg_speed"] = random.uniform(25, 35)
                lane_data["queue_length"] = max(0, lane_data["queue_length"] - 1)
            else:
                # Vehicles accumulating
                lane_data["vehicle_count"] += random.randint(0, 2)
                lane_data["avg_speed"] = random.uniform(5, 20)
                lane_data["queue_length"] += random.randint(0, 1)
                
            # Decrease timer
            lane_data["time_remaining"] = max(0, lane_data["time_remaining"] - 2)
        
        return {
            "ai_decision": f"Priority given to {priority_direction} direction",
            "reason": f"Highest vehicle count: {max_vehicles}",
            "confidence": round(random.uniform(0.85, 0.98), 3),
            "processing_time_ms": random.randint(8, 15)
        }

    def generate_live_metrics(self) -> Dict[str, Any]:
        """Generate live metrics data"""
        
        # Calculate aggregated metrics
        total_vehicles = sum(lane["vehicle_count"] for lane in self.lanes.values())
        avg_wait_time = sum(lane["time_remaining"] for lane in self.lanes.values()) / len(self.lanes)
        avg_speed = sum(lane["avg_speed"] for lane in self.lanes.values()) / len(self.lanes)
        
        # Environmental calculations (simulated)
        fuel_saved = total_vehicles * random.uniform(0.1, 0.3)  # liters
        co2_saved = fuel_saved * 2.3  # kg CO2 per liter
        
        return {
            "timestamp": datetime.now().isoformat(),
            "wait_times": {
                "overall_avg_wait_time": round(avg_wait_time, 1),
                "best_performance": min(lane["time_remaining"] for lane in self.lanes.values()),
                "worst_performance": max(lane["time_remaining"] for lane in self.lanes.values()),
                "detailed_data": [
                    {
                        "intersection_id": INTERSECTION_ID,
                        "simulation_id": "test_sim_001",
                        "avg_wait_time": lane["time_remaining"],
                        "total_vehicles": lane["vehicle_count"]
                    } for lane in self.lanes.values()
                ],
                "total_intersections": 1
            },
            "speeds": {
                "overall_avg_speed": round(avg_speed, 1),
                "speed_data": [
                    {
                        "intersection_id": INTERSECTION_ID,
                        "simulation_id": "test_sim_001",
                        "avg_speed": lane["avg_speed"],
                        "avg_throughput": lane["vehicle_count"] * 2.5,
                        "total_vehicles": lane["vehicle_count"]
                    } for lane in self.lanes.values()
                ]
            },
            "environmental_impact": {
                "environmental_data": [
                    {
                        "intersection_id": INTERSECTION_ID,
                        "simulation_id": "test_sim_001", 
                        "co2_saved": co2_saved / 4,
                        "fuel_saved": fuel_saved / 4
                    } for _ in range(4)  # One for each direction
                ],
                "total_fuel_saved": round(fuel_saved, 2),
                "total_co2_saved": round(co2_saved, 2)
            }
        }

    def generate_signal_timings(self) -> Dict[str, Any]:
        """Generate signal timing data"""
        return {
            "intersection_id": INTERSECTION_ID,
            "signals": [
                {
                    "lane_id": lane_id,
                    "direction": lane_data["direction"],
                    "type": lane_data["type"],
                    "current_light": lane_data["current_light"],
                    "time_remaining": lane_data["time_remaining"],
                    "max_time": lane_data["max_time"],
                    "vehicle_count": lane_data["vehicle_count"]
                } for lane_id, lane_data in self.lanes.items()
            ],
            "timestamp": datetime.now().isoformat(),
            "cycle_number": self.current_cycle,
            "ai_status": "active"
        }

    def post_to_backend(self, endpoint: str, data: Dict[str, Any]) -> bool:
        """Post data to backend endpoint"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Posted to {endpoint} - Status: {response.status_code}")
                return True
            else:
                print(f"⚠️ Failed to post to {endpoint} - Status: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error posting to {endpoint}: {e}")
            return False
    
    def test_get_endpoint(self, endpoint: str) -> bool:
        """Test GET endpoint"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ GET {endpoint} - Status: {response.status_code}")
                return True
            else:
                print(f"⚠️ Failed GET {endpoint} - Status: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting {endpoint}: {e}")
            return False

    def run_simulation_cycle(self):
        """Run one simulation cycle"""
        cycle_start = datetime.now()
        
        # 1. Simulate AI decision making
        ai_decision = self.simulate_ai_decision()
        
        # 2. Generate live metrics
        live_metrics = self.generate_live_metrics()
        
        # 3. Generate signal timings
        signal_timings = self.generate_signal_timings()
        
        # 4. Post data to backend
        print(f"\n🔄 Cycle {self.current_cycle} - {cycle_start.strftime('%H:%M:%S')}")
        print(f"🤖 AI Decision: {ai_decision['ai_decision']}")
        print(f"📊 Total Vehicles: {sum(lane['vehicle_count'] for lane in self.lanes.values())}")
        
        # Test the endpoints that the frontend actually uses
        success_count = 0
        
        # Test GET live metrics (what frontend calls)
        if self.test_get_endpoint("/api/v1/dashboard/live-metrics"):
            success_count += 1
            
        # Test health endpoint
        if self.test_get_endpoint("/health"):
            success_count += 1
        
        # Test simulation data ingestion (POST)
        simulation_data = {
            "data": {
                "intersection_id": INTERSECTION_ID,
                "timestamp": datetime.now().isoformat(),
                "signals": signal_timings["signals"],
                "ai_decision": ai_decision,
                "metrics": live_metrics
            }
        }
        
        if self.post_to_backend("/api/v1/ingest/simulation", simulation_data):
            success_count += 1
            
        # Show current signal states
        signal_states = []
        for lane_id, lane_data in self.lanes.items():
            light_emoji = "🟢" if lane_data["current_light"] == "green" else "🔴" if lane_data["current_light"] == "red" else "🟡"
            signal_states.append(f"{lane_id}: {light_emoji} ({lane_data['time_remaining']}s, {lane_data['vehicle_count']} cars)")
        
        print("🚦 Signal States:")
        for state in signal_states:
            print(f"   {state}")
            
        print(f"📡 Tested {success_count}/3 endpoints successfully")
        
        self.current_cycle += 1

    def start_simulation(self):
        """Start the continuous simulation"""
        print(f"🚀 Starting Real-time Traffic Simulation...")
        print(f"💡 Dashboard should be running at: {FRONTEND_URL}")
        print(f"🔧 Backend should be running at: {BACKEND_URL}")
        print(f"⏰ Updates every {UPDATE_INTERVAL} seconds")
        print("=" * 60)
        
        try:
            while True:
                self.run_simulation_cycle()
                time.sleep(UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Simulation stopped by user")
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")

def test_backend_connection():
    """Test if backend is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend is running at {BACKEND_URL}")
            return True
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ Backend is not available at {BACKEND_URL}")
        print(f"💡 Please start your backend first: python fastapi_main.py")
        return False

if __name__ == "__main__":
    print("🚦 SIH Traffic Dashboard - Real-time Data Simulator")
    print("=" * 60)
    
    # Test backend connection first
    if not test_backend_connection():
        print("\n🛑 Please start the backend server first!")
        exit(1)
    
    # Create and start simulator
    simulator = TrafficSimulator()
    simulator.start_simulation()