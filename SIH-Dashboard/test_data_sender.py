#!/usr/bin/env python3
"""
Test Data Sender for Traffic Dashboard Integration

This script sends realistic simulation data to the FastAPI backend
to test the real-time dashboard integration.

Usage:
    python test_data_sender.py
"""

import requests
import json
import time
import random
from datetime import datetime, timezone
from typing import Dict, Any
import sys

# Configuration
API_BASE_URL = "http://localhost:8000"
SIMULATION_ID = "TEST_SIM_001"
INTERSECTION_ID = "INT_TEST_001"
UPDATE_INTERVAL = 3  # seconds between updates

class TrafficSimulationTester:
    def __init__(self):
        self.api_url = API_BASE_URL
        self.simulation_id = SIMULATION_ID
        self.intersection_id = INTERSECTION_ID
        self.current_phase = 0  # 0 = East-West, 1 = North-South
        self.phase_timer = 30  # seconds remaining in current phase
        self.total_vehicles_passed = 0
        
        # Vehicle counts per direction
        self.vehicle_counts = {
            "east": {"car": 5, "bus": 1, "truck": 2, "bike": 3},
            "west": {"car": 7, "bus": 0, "truck": 1, "bike": 4},
            "north": {"car": 8, "bus": 2, "truck": 0, "bike": 2},
            "south": {"car": 6, "bus": 1, "truck": 1, "bike": 5}
        }
        
        # Queue lengths per direction
        self.queue_lengths = {
            "east": 5, "west": 8, "north": 12, "south": 7
        }
        
        # Vehicles crossed counters
        self.vehicles_crossed = {
            "east": 0, "west": 0, "north": 0, "south": 0
        }
        
        # Wait times per direction
        self.wait_times = {
            "east": 15.5, "west": 18.2, "north": 22.8, "south": 16.9
        }

    def check_backend_health(self) -> bool:
        """Check if the FastAPI backend is running"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Backend is healthy: {health_data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to backend at {self.api_url}")
            print("   Make sure FastAPI server is running: uvicorn app.main:app --reload")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    def simulate_traffic_changes(self):
        """Simulate realistic traffic changes"""
        for direction in self.vehicle_counts:
            # Simulate vehicles arriving and leaving
            arrival_rate = random.randint(0, 3)  # 0-3 new vehicles
            departure_rate = random.randint(0, 2)  # 0-2 vehicles leave
            
            # Update vehicle counts randomly
            for vehicle_type in self.vehicle_counts[direction]:
                if random.random() < 0.3:  # 30% chance of change
                    change = random.randint(-1, 2)
                    self.vehicle_counts[direction][vehicle_type] = max(0, 
                        self.vehicle_counts[direction][vehicle_type] + change)
            
            # Update queue lengths
            total_vehicles = sum(self.vehicle_counts[direction].values())
            self.queue_lengths[direction] = max(0, total_vehicles - random.randint(0, 3))
            
            # Update wait times (simulate traffic improvements/delays)
            wait_change = random.uniform(-2.0, 3.0)
            self.wait_times[direction] = max(5.0, self.wait_times[direction] + wait_change)

    def update_phase_system(self):
        """Update traffic signal phases"""
        self.phase_timer -= UPDATE_INTERVAL
        
        if self.phase_timer <= 0:
            # Switch phases
            self.current_phase = 1 - self.current_phase
            
            # Reset timer based on traffic density
            if self.current_phase == 0:  # East-West phase
                density = (sum(self.vehicle_counts["east"].values()) + 
                          sum(self.vehicle_counts["west"].values()))
                self.phase_timer = min(45, max(15, density * 2))
            else:  # North-South phase
                density = (sum(self.vehicle_counts["north"].values()) + 
                          sum(self.vehicle_counts["south"].values()))
                self.phase_timer = min(45, max(15, density * 2))
            
            print(f"🚥 Phase switched to: {'East-West' if self.current_phase == 0 else 'North-South'}")
            
            # Simulate vehicles crossing during green phase
            active_directions = ["east", "west"] if self.current_phase == 0 else ["north", "south"]
            for direction in active_directions:
                crossed = random.randint(2, 8)
                self.vehicles_crossed[direction] += crossed
                self.total_vehicles_passed += crossed

    def generate_simulation_data(self) -> Dict[Any, Any]:
        """Generate realistic simulation data"""
        # Update traffic simulation
        self.simulate_traffic_changes()
        self.update_phase_system()
        
        # Determine active directions and status
        active_directions = ["east", "west"] if self.current_phase == 0 else ["north", "south"]
        
        # Determine phase status
        if self.phase_timer <= 3:
            status = "YELLOW"
        elif self.phase_timer > 0:
            status = "GREEN"
        else:
            status = "RED"
        
        # Create direction metrics
        direction_metrics = {}
        for direction in ["east", "west", "north", "south"]:
            # Add some randomness for emergency vehicles (rare)
            emergency_present = random.random() < 0.05  # 5% chance
            
            direction_metrics[direction] = {
                "vehicle_counts": self.vehicle_counts[direction].copy(),
                "queue_length": self.queue_lengths[direction],
                "vehicles_crossed": self.vehicles_crossed[direction],
                "avg_wait_time": round(self.wait_times[direction], 1),
                "emergency_vehicle_present": emergency_present
            }
        
        # Calculate overall metrics
        all_wait_times = list(self.wait_times.values())
        avg_wait_time_all = sum(all_wait_times) / len(all_wait_times)
        
        # Calculate throughput (vehicles per minute)
        elapsed_minutes = max(1, (time.time() - getattr(self, 'start_time', time.time())) / 60)
        throughput = self.total_vehicles_passed / elapsed_minutes
        
        # Generate the complete simulation data
        simulation_data = {
            "simulation_id": self.simulation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "intersection_id": self.intersection_id,
            "current_phase": {
                "phase_id": self.current_phase,
                "active_directions": active_directions,
                "status": status,
                "remaining_time": max(0, self.phase_timer)
            },
            "direction_metrics": direction_metrics,
            "overall_metrics": {
                "total_vehicles_passed": self.total_vehicles_passed,
                "avg_wait_time_all_sides": round(avg_wait_time_all, 1),
                "throughput": round(throughput, 2),
                "avg_speed": round(random.uniform(20.0, 35.0), 1),  # Simulated average speed
                "cycle_time": round(self.phase_timer + random.uniform(30, 60), 1)
            }
        }
        
        return simulation_data

    def send_data_to_backend(self, data: Dict[Any, Any]) -> bool:
        """Send simulation data to FastAPI backend"""
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/ingest/simulation",
                json={"data": data},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return True
            else:
                print(f"❌ Failed to send data: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout - backend might be slow")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - is the backend running?")
            return False
        except Exception as e:
            print(f"❌ Error sending data: {e}")
            return False

    def print_data_summary(self, data: Dict[Any, Any]):
        """Print a summary of the data being sent"""
        current_phase = data["current_phase"]
        overall = data["overall_metrics"]
        
        print(f"\n📊 Simulation Update #{getattr(self, 'update_count', 0)}")
        print(f"   🕒 Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"   🚦 Phase: {current_phase['active_directions']} ({current_phase['status']})")
        print(f"   ⏱️  Remaining: {current_phase['remaining_time']:.1f}s")
        print(f"   🚗 Total Vehicles Passed: {overall['total_vehicles_passed']}")
        print(f"   ⏳ Avg Wait Time: {overall['avg_wait_time_all_sides']}s")
        print(f"   📈 Throughput: {overall['throughput']} v/min")
        
        # Show vehicle counts
        direction_metrics = data["direction_metrics"]
        for direction, metrics in direction_metrics.items():
            total_vehicles = sum(metrics["vehicle_counts"].values())
            queue = metrics["queue_length"]
            emergency = "🚨" if metrics["emergency_vehicle_present"] else ""
            print(f"   {direction.upper()}: {total_vehicles} vehicles, queue: {queue} {emergency}")

    def run_continuous_test(self):
        """Run continuous testing with regular updates"""
        print("🚀 Starting Traffic Simulation Data Sender")
        print(f"📡 Backend URL: {self.api_url}")
        print(f"🔄 Update Interval: {UPDATE_INTERVAL} seconds")
        print("Press Ctrl+C to stop\n")
        
        if not self.check_backend_health():
            return
        
        self.start_time = time.time()
        update_count = 0
        
        try:
            while True:
                update_count += 1
                self.update_count = update_count
                
                # Generate and send data
                data = self.generate_simulation_data()
                self.print_data_summary(data)
                
                success = self.send_data_to_backend(data)
                if success:
                    print("✅ Data sent successfully!")
                else:
                    print("❌ Failed to send data")
                
                print("-" * 50)
                
                # Wait for next update
                time.sleep(UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping simulation data sender...")
            print(f"📊 Total updates sent: {update_count}")
            print(f"🚗 Total vehicles processed: {self.total_vehicles_passed}")

    def send_single_test(self):
        """Send a single test data point"""
        print("🧪 Sending single test data to backend...")
        
        if not self.check_backend_health():
            return
        
        data = self.generate_simulation_data()
        self.print_data_summary(data)
        
        print("\n📤 Sending data to backend...")
        success = self.send_data_to_backend(data)
        
        if success:
            print("✅ Test data sent successfully!")
            print("\n🌐 Check your React dashboard at: http://localhost:3000")
            print("🔗 WebSocket should show real-time updates")
        else:
            print("❌ Failed to send test data")

def main():
    """Main function with command line options"""
    tester = TrafficSimulationTester()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "single":
            tester.send_single_test()
        elif sys.argv[1] == "continuous":
            tester.run_continuous_test()
        else:
            print("Usage: python test_data_sender.py [single|continuous]")
    else:
        # Interactive mode
        print("🚦 Traffic Simulation Data Sender")
        print("\nChoose mode:")
        print("1. Send single test data")
        print("2. Continuous data sending")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            tester.send_single_test()
        elif choice == "2":
            tester.run_continuous_test()
        elif choice == "3":
            print("👋 Goodbye!")
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()