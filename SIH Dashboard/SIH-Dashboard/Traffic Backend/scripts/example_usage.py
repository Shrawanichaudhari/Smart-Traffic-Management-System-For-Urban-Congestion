#!/usr/bin/env python3
"""
Example usage script for Traffic Analytics API.
Demonstrates how to use the API endpoints with sample data.
"""

import asyncio
import requests
import json
from datetime import datetime
import time

API_BASE_URL = "http://localhost:8000"

# Sample simulation data
SAMPLE_SIMULATION_DATA = {
    "simulation_id": "SIM_001_EXAMPLE",
    "timestamp": "2023-12-01T10:00:00Z",
    "intersection_id": "INT_001", 
    "signals": [
        {
            "direction": "north",
            "vehicle_counts": {
                "car": 15,
                "bus": 2,
                "truck": 1,
                "bike": 3,
                "rickshaw": 0
            },
            "emergency_vehicle_present": False,
            "signal_status": "GREEN", 
            "signal_timer": 25,
            "vehicles_crossed": 12,
            "avg_wait_time": 18.5,
            "green_time_allocated": 45,
            "queue_length": 4
        },
        {
            "direction": "south", 
            "vehicle_counts": {
                "car": 22,
                "bus": 1,
                "truck": 2,
                "bike": 1,
                "rickshaw": 1
            },
            "emergency_vehicle_present": False,
            "signal_status": "RED",
            "signal_timer": 15,
            "vehicles_crossed": 8,
            "avg_wait_time": 32.1,
            "green_time_allocated": None,
            "queue_length": 7
        },
        {
            "direction": "east",
            "vehicle_counts": {
                "car": 18,
                "bus": 0,
                "truck": 1,
                "bike": 2,
                "rickshaw": 0
            },
            "emergency_vehicle_present": True,
            "signal_status": "GREEN",
            "signal_timer": 35,
            "vehicles_crossed": 15,
            "avg_wait_time": 12.3,
            "green_time_allocated": 60,
            "queue_length": 2
        },
        {
            "direction": "west",
            "vehicle_counts": {
                "car": 20,
                "bus": 1,
                "truck": 0,
                "bike": 4,
                "rickshaw": 2
            },
            "emergency_vehicle_present": False,
            "signal_status": "RED",
            "signal_timer": 25,
            "vehicles_crossed": 10,
            "avg_wait_time": 28.7,
            "green_time_allocated": None,
            "queue_length": 6
        }
    ],
    "metrics": {
        "total_vehicles_passed": 45,
        "avg_wait_time_all_sides": 22.9,
        "throughput": 0.75,
        "avg_speed": 28.5,
        "fuel_saved": 3.2,
        "co2_saved": 7.36,
        "emergency_overrides": 1,
        "cycle_time": 120
    }
}

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False

def test_system_info():
    """Test the system info endpoint."""
    print("🔍 Testing system info...")
    try:
        response = requests.get(f"{API_BASE_URL}/system/info")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Database URL: {data['database'].get('url', 'Hidden')}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ System info failed: {e}")
        return False

def test_data_ingestion():
    """Test data ingestion endpoint."""
    print("🔍 Testing data ingestion...")
    try:
        payload = {"data": SAMPLE_SIMULATION_DATA}
        response = requests.post(f"{API_BASE_URL}/api/v1/ingest/simulation", json=payload)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Ingestion result: {data.get('status', 'Unknown')}")
            print(f"   Records inserted: {data.get('records_inserted', {})}")
        else:
            print(f"   Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Data ingestion failed: {e}")
        return False

def test_analytics_endpoints():
    """Test various analytics endpoints."""
    print("🔍 Testing analytics endpoints...")
    
    endpoints = [
        "/api/v1/analytics/wait-times",
        "/api/v1/analytics/environmental-impact", 
        "/api/v1/analytics/comparison/baseline-vs-ai",
        f"/api/v1/simulations/{SAMPLE_SIMULATION_DATA['simulation_id']}"
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            results[endpoint] = response.status_code
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"     Note: {data['error']}")
                    
        except Exception as e:
            print(f"   ❌ {endpoint} failed: {e}")
            results[endpoint] = 0
    
    return all(status in [200, 404] for status in results.values())

def test_dashboard_endpoints():
    """Test dashboard endpoints."""
    print("🔍 Testing dashboard endpoints...")
    
    endpoints = [
        "/api/v1/dashboard/live-metrics",
        "/api/v1/dashboard/performance-comparison"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"     Keys: {list(data.keys())}")
                
        except Exception as e:
            print(f"   ❌ {endpoint} failed: {e}")

def generate_sample_batch_data():
    """Generate a batch of sample simulation data."""
    print("🔍 Testing batch ingestion...")
    
    batch_data = []
    for i in range(3):
        data = SAMPLE_SIMULATION_DATA.copy()
        data["simulation_id"] = f"SIM_BATCH_{i:03d}"
        data["timestamp"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        # Vary the metrics slightly
        data["metrics"]["avg_wait_time_all_sides"] += i * 2.0
        data["metrics"]["fuel_saved"] += i * 0.5
        batch_data.append(data)
    
    try:
        payload = {"data_list": batch_data}
        response = requests.post(f"{API_BASE_URL}/api/v1/ingest/batch", json=payload)
        print(f"   Batch ingestion status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Batch result: {data.get('batch_status')}")
            print(f"   Successful: {data.get('successful')}/{data.get('total_processed')}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Batch ingestion failed: {e}")

def main():
    """Run comprehensive API testing."""
    print("🚀 Starting Traffic Analytics API Testing...")
    print("=" * 50)
    
    # Test basic health and connectivity
    if not test_health_check():
        print("❌ Health check failed. Make sure the API is running!")
        return
    
    print()
    test_system_info()
    print()
    
    # Test data ingestion
    test_data_ingestion()
    print()
    
    # Wait a moment for data to be processed
    print("⏳ Waiting for data processing...")
    time.sleep(2)
    
    # Test analytics
    test_analytics_endpoints()
    print()
    
    # Test dashboard
    test_dashboard_endpoints()
    print()
    
    # Test batch operations
    generate_sample_batch_data()
    print()
    
    print("=" * 50)
    print("✅ API testing completed!")
    print()
    print("🔗 Useful URLs:")
    print(f"   API Documentation: {API_BASE_URL}/docs")
    print(f"   Health Check: {API_BASE_URL}/health")
    print(f"   System Info: {API_BASE_URL}/system/info")

if __name__ == "__main__":
    main()
