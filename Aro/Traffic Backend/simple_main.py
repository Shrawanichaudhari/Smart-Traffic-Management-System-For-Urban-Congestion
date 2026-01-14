from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import random

# Create FastAPI app
app = FastAPI(title="Traffic Analytics API", version="1.0.0")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data generators
def generate_wait_times():
    return {
        "overall_avg_wait_time": round(random.uniform(30, 80), 1),
        "best_performance": round(random.uniform(15, 25), 1),
        "worst_performance": round(random.uniform(70, 100), 1),
        "detailed_data": [
            {
                "intersection_id": f"intersection_{i}",
                "simulation_id": "sim_001",
                "avg_wait_time": round(random.uniform(20, 90), 1),
                "total_vehicles": random.randint(50, 200)
            } for i in range(1, 5)
        ],
        "total_intersections": 4
    }

def generate_speeds():
    return {
        "overall_avg_speed": round(random.uniform(25, 45), 1),
        "speed_data": [
            {
                "intersection_id": f"intersection_{i}",
                "simulation_id": "sim_001",
                "avg_speed": round(random.uniform(20, 50), 1),
                "avg_throughput": round(random.uniform(100, 300), 1),
                "total_vehicles": random.randint(50, 200)
            } for i in range(1, 5)
        ]
    }

def generate_environmental():
    return {
        "environmental_data": [
            {
                "intersection_id": f"intersection_{i}",
                "simulation_id": "sim_001",
                "co2_saved": round(random.uniform(100, 500), 1),
                "fuel_saved": round(random.uniform(50, 200), 1)
            } for i in range(1, 5)
        ],
        "total_fuel_saved": round(random.uniform(200, 800), 1),
        "total_co2_saved": round(random.uniform(400, 1600), 1)
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "timestamp": datetime.now().isoformat(),
        "service": "traffic-analytics-api"
    }

# System info endpoint
@app.get("/system/info")
def system_info():
    return {
        "database": {"status": "connected", "type": "mock"},
        "service_info": {
            "name": "Smart Traffic Analytics API",
            "version": "1.0.0",
            "uptime": "running"
        }
    }

# Main dashboard endpoint that your frontend calls
@app.get("/api/v1/dashboard/live-metrics")
def get_live_metrics():
    return {
        "timestamp": datetime.now().isoformat(),
        "wait_times": generate_wait_times(),
        "speeds": generate_speeds(),
        "environmental_impact": generate_environmental()
    }

# Performance comparison endpoint
@app.get("/api/v1/dashboard/performance-comparison")
def get_performance_comparison():
    return {
        "comparison": {
            "comparison_data": {
                "ai_mode": {
                    "avg_wait_time": round(random.uniform(30, 40), 1),
                    "avg_throughput": round(random.uniform(250, 300), 1),
                    "avg_speed": round(random.uniform(35, 45), 1),
                    "total_fuel_saved": round(random.uniform(150, 250), 1)
                },
                "baseline_mode": {
                    "avg_wait_time": round(random.uniform(60, 80), 1),
                    "avg_throughput": round(random.uniform(150, 200), 1),
                    "avg_speed": round(random.uniform(20, 30), 1),
                    "total_fuel_saved": 0
                }
            }
        },
        "emergency_handling": {
            "response_time": round(random.uniform(15, 30), 1),
            "incidents_handled": random.randint(5, 20)
        },
        "generated_at": datetime.now().isoformat()
    }

# Analytics endpoints
@app.get("/api/v1/analytics/wait-times")
def get_wait_times():
    return generate_wait_times()

@app.get("/api/v1/analytics/speeds")
def get_speeds():
    return generate_speeds()

@app.get("/api/v1/analytics/environmental-impact")
def get_environmental_impact():
    return generate_environmental()

# Chart data endpoints
@app.get("/api/v1/charts/wait-time-trend")
def get_wait_time_trend():
    simulation_ids = ["sim_001"]  # Default
    
    datasets = []
    for sim_id in simulation_ids:
        data_points = []
        for i in range(24):  # 24 hours of data
            timestamp = datetime.now().replace(hour=i, minute=0, second=0).isoformat()
            data_points.append({
                "timestamp": timestamp,
                "avg_wait_time": round(random.uniform(20, 80), 1)
            })
        
        datasets.append({
            "simulation_id": sim_id,
            "data": data_points
        })
    
    return {
        "chart_type": "line",
        "datasets": datasets,
        "x_axis": "timestamp",
        "y_axis": "avg_wait_time",
        "time_window_hours": 24
    }

# Data ingestion endpoint
@app.post("/api/v1/ingest/simulation")
def ingest_simulation_data(request: dict):
    # Just return success for now
    return {
        "message": "Data ingested successfully",
        "result": {"status": "success", "data_id": "mock_id"}
    }

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )