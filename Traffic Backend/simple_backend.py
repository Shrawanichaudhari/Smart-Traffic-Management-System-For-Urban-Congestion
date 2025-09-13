from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import random
from datetime import datetime
import logging
from threading import Timer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("traffic_api")

# Initialize FastAPI app
app = FastAPI(
    title="Smart Traffic Signal Analytics API",
    description="Backend API for AI-powered traffic signal simulation analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock signal states for testing
signal_states = {
    "INT_001": {
        "n-straight": {"current_light": "red", "time_remaining": 25, "max_time": 30, "vehicle_count": 8},
        "s-straight": {"current_light": "red", "time_remaining": 35, "max_time": 45, "vehicle_count": 12},
        "e-straight": {"current_light": "green", "time_remaining": 15, "max_time": 45, "vehicle_count": 15},
        "w-straight": {"current_light": "red", "time_remaining": 20, "max_time": 45, "vehicle_count": 9}
    }
}

# Background task to simulate signal changes
def update_signal_states():
    """Update signal states every 2 seconds to simulate real traffic"""
    for intersection_id in signal_states:
        for lane_id, lane_data in signal_states[intersection_id].items():
            # Decrease timer
            lane_data["time_remaining"] = max(0, lane_data["time_remaining"] - 2)
            
            # Update vehicle count
            if lane_data["current_light"] == "green":
                # Vehicles passing through
                lane_data["vehicle_count"] = max(0, lane_data["vehicle_count"] - random.randint(0, 2))
            else:
                # Vehicles accumulating
                lane_data["vehicle_count"] += random.randint(0, 1)
            
            # Simple AI logic: change lights when timer expires
            if lane_data["time_remaining"] <= 0:
                if lane_data["current_light"] == "green":
                    lane_data["current_light"] = "red"
                    lane_data["time_remaining"] = random.randint(20, 45)
                elif lane_data["vehicle_count"] > 10:  # AI decides to turn green if many vehicles
                    lane_data["current_light"] = "green" 
                    lane_data["time_remaining"] = lane_data["max_time"]
                else:
                    lane_data["time_remaining"] = random.randint(10, 30)
    
    # Schedule next update
    Timer(2.0, update_signal_states).start()

# Start the background simulation
Timer(2.0, update_signal_states).start()

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "not_configured",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "traffic-analytics-api",
        "using_real_db": False
    }

# System info endpoint
@app.get("/system/info")
def system_info():
    """Get system information and connection stats."""
    return {
        "database": {"status": "connected", "type": "mock"},
        "service_info": {
            "name": "Smart Traffic Analytics API",
            "version": "1.0.0",
            "uptime": "running"
        }
    }

# Generate mock live metrics
@app.get("/api/v1/dashboard/live-metrics")
def get_live_metrics():
    """Get live metrics for dashboard display."""
    # Calculate aggregated metrics from signal states
    total_vehicles = sum(lane["vehicle_count"] for intersection in signal_states.values() for lane in intersection.values())
    avg_wait_time = sum(lane["time_remaining"] for intersection in signal_states.values() for lane in intersection.values()) / 4
    avg_speed = random.uniform(20, 40)
    
    # Environmental calculations
    fuel_saved = total_vehicles * random.uniform(0.1, 0.3)
    co2_saved = fuel_saved * 2.3
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "wait_times": {
            "overall_avg_wait_time": round(avg_wait_time, 1),
            "best_performance": min(lane["time_remaining"] for intersection in signal_states.values() for lane in intersection.values()),
            "worst_performance": max(lane["time_remaining"] for intersection in signal_states.values() for lane in intersection.values()),
            "detailed_data": [
                {
                    "intersection_id": "INT_001",
                    "simulation_id": "test_sim_001",
                    "avg_wait_time": lane["time_remaining"],
                    "total_vehicles": lane["vehicle_count"]
                } for lane in signal_states["INT_001"].values()
            ],
            "total_intersections": 1
        },
        "speeds": {
            "overall_avg_speed": round(avg_speed, 1),
            "speed_data": [
                {
                    "intersection_id": "INT_001",
                    "simulation_id": "test_sim_001",
                    "avg_speed": random.uniform(15, 35),
                    "avg_throughput": lane["vehicle_count"] * 2.5,
                    "total_vehicles": lane["vehicle_count"]
                } for lane in signal_states["INT_001"].values()
            ]
        },
        "environmental_impact": {
            "environmental_data": [
                {
                    "intersection_id": "INT_001",
                    "simulation_id": "test_sim_001",
                    "co2_saved": co2_saved / 4,
                    "fuel_saved": fuel_saved / 4
                } for _ in range(4)
            ],
            "total_fuel_saved": round(fuel_saved, 2),
            "total_co2_saved": round(co2_saved, 2)
        }
    }

# Signal timing endpoint
@app.get("/api/v1/signals/timings")
def get_signal_timings(intersection_id: Optional[str] = Query(None)):
    """Get current signal timings and states"""
    try:
        intersection_id = intersection_id or "INT_001"
        
        if intersection_id not in signal_states:
            signal_states[intersection_id] = signal_states["INT_001"].copy()
            
        signals = []
        for lane_id, lane_data in signal_states[intersection_id].items():
            direction = lane_id.split("-")[0]
            direction_map = {"n": "north", "s": "south", "e": "east", "w": "west"}
            
            signals.append({
                "lane_id": lane_id,
                "direction": direction_map.get(direction, direction),
                "type": "straight",
                "current_light": lane_data["current_light"],
                "time_remaining": lane_data["time_remaining"],
                "max_time": lane_data["max_time"],
                "vehicle_count": lane_data["vehicle_count"]
            })
            
        return {
            "intersection_id": intersection_id,
            "signals": signals,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_status": "active"
        }
        
    except Exception as e:
        logger.error(f"Signal timings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Manual signal override
@app.post("/api/v1/signals/manual-override")
def manual_signal_override(request: dict):
    """Manual signal override"""
    try:
        lane_id = request["lane_id"]
        signal_state = request["signal_state"]
        duration = request.get("duration", 30)
        
        # Update signal state
        for intersection_id in signal_states:
            if lane_id in signal_states[intersection_id]:
                signal_states[intersection_id][lane_id]["current_light"] = signal_state
                signal_states[intersection_id][lane_id]["time_remaining"] = duration
                break
        
        logger.info(f"Manual override: {lane_id} -> {signal_state} for {duration}s")
        
        return {
            "success": True,
            "message": f"Signal {lane_id} changed to {signal_state}",
            "lane_id": lane_id,
            "signal_state": signal_state,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Manual override error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Emergency override
@app.post("/api/v1/signals/emergency-override")
def emergency_override(request: dict):
    """Emergency vehicle override"""
    try:
        lane_id = request["lane_id"]
        duration = request.get("duration", 60)
        
        # Set emergency lane to green, others to red
        for intersection_id in signal_states:
            for lid, lane_data in signal_states[intersection_id].items():
                if lid == lane_id:
                    lane_data["current_light"] = "green"
                    lane_data["time_remaining"] = duration
                else:
                    lane_data["current_light"] = "red"
                    lane_data["time_remaining"] = duration
                    
        logger.info(f"Emergency override: {lane_id} priority for {duration}s")
        
        return {
            "success": True,
            "message": f"Emergency route cleared for {lane_id}",
            "priority_lane": lane_id,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Emergency override error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Reset to AI control
@app.post("/api/v1/signals/reset-ai")
def reset_to_ai(request: dict):
    """Reset signals to AI control"""
    try:
        intersection_id = request.get("intersection_id", "INT_001")
        
        # Reset to default AI-controlled state
        if intersection_id in signal_states:
            signal_states[intersection_id] = {
                "n-straight": {"current_light": "red", "time_remaining": 25, "max_time": 30, "vehicle_count": 8},
                "s-straight": {"current_light": "red", "time_remaining": 35, "max_time": 45, "vehicle_count": 12}, 
                "e-straight": {"current_light": "green", "time_remaining": 15, "max_time": 45, "vehicle_count": 15},
                "w-straight": {"current_light": "red", "time_remaining": 20, "max_time": 45, "vehicle_count": 9}
            }
            
        logger.info(f"Reset to AI control: {intersection_id}")
        
        return {
            "success": True,
            "message": "Traffic signals returned to AI control",
            "intersection_id": intersection_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Reset AI error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data ingestion endpoint
@app.post("/api/v1/ingest/simulation")
def ingest_simulation_data(request: dict):
    """Ingest simulation data"""
    try:
        return {
            "message": "Data ingested successfully",
            "result": {"status": "success", "data_id": "mock_id"}
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=400, detail=f"Ingestion failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)