from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import random
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_backend")

# Pydantic models for ML data ingestion
class VehicleCounts(BaseModel):
    car: int
    bus: int
    truck: int
    bike: int

class DirectionMetric(BaseModel):
    vehicle_counts: VehicleCounts
    queue_length: int
    vehicles_crossed: int
    avg_wait_time: float
    emergency_vehicle_present: bool

class CurrentPhase(BaseModel):
    phase_id: int
    active_directions: List[str]
    status: str
    remaining_time: int

class OverallMetrics(BaseModel):
    total_vehicles_passed: int
    avg_wait_time_all_sides: float
    throughput: float
    avg_speed: float
    cycle_time: int

class MLTrafficData(BaseModel):
    simulation_id: str
    timestamp: str
    intersection_id: str
    current_phase: CurrentPhase
    direction_metrics: Dict[str, DirectionMetric]
    overall_metrics: OverallMetrics

# Global storage for ML data
ml_traffic_data: Optional[MLTrafficData] = None
last_ml_update: Optional[datetime] = None

# ML API configuration
ML_API_BASE_URL = "http://localhost:8000/api/v1"
ML_INGEST_ENDPOINT = f"{ML_API_BASE_URL}/ingest/simulation"

# HTTP client for API requests
httpx_client = httpx.AsyncClient(timeout=5.0)

async def fetch_ml_data() -> Optional[Dict[str, Any]]:
    """Fetch ML traffic data from the existing API endpoint"""
    global ml_traffic_data, last_ml_update
    
    try:
        logger.info(f"Fetching ML data from {ML_INGEST_ENDPOINT}")
        response = await httpx_client.get(ML_INGEST_ENDPOINT)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate and store the ML data
            try:
                ml_traffic_data = MLTrafficData(**data)
                last_ml_update = datetime.now()
                logger.info(f"Successfully updated ML data for intersection {ml_traffic_data.intersection_id}")
                return data
            except Exception as validation_error:
                logger.error(f"ML data validation error: {validation_error}")
                return None
        else:
            logger.warning(f"ML API returned status {response.status_code}: {response.text}")
            return None
            
    except httpx.TimeoutException:
        logger.warning("Timeout while fetching ML data")
        return None
    except httpx.ConnectError:
        logger.warning("Could not connect to ML API - using fallback data")
        return None
    except Exception as e:
        logger.error(f"Error fetching ML data: {e}")
        return None

app = FastAPI(title="Traffic WebSocket API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Mock traffic data that matches your database models
intersection_data = {
    "intersection_id": "INT_001",
    "lanes": {
        "n-straight": {
            "lane_id": "n-straight",
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
            "lane_id": "s-straight", 
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
            "lane_id": "e-straight",
            "direction": "east", 
            "type": "straight",
            "current_light": "green",
            "time_remaining": 15,
            "max_time": 45,
            "vehicle_count": 15,
            "avg_speed": 32.1,
            "queue_length": 2
        },
        "w-straight": {
            "lane_id": "w-straight",
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
}

def update_intersection_data():
    """Simulate real-time traffic changes (like data from your database)"""
    
    for lane_id, lane in intersection_data["lanes"].items():
        # Decrease timers
        lane["time_remaining"] = max(0, lane["time_remaining"] - 1)
        
        # Update vehicle counts and speeds based on signal state
        if lane["current_light"] == "green":
            # Vehicles moving through
            lane["vehicle_count"] = max(0, lane["vehicle_count"] - random.randint(0, 2))
            lane["avg_speed"] = random.uniform(25, 45)
            lane["queue_length"] = max(0, lane["queue_length"] - random.randint(0, 1))
        else:
            # Vehicles accumulating
            lane["vehicle_count"] += random.randint(0, 2)
            lane["avg_speed"] = random.uniform(5, 25)
            lane["queue_length"] += random.randint(0, 1)
        
        # AI signal control logic
        if lane["time_remaining"] <= 0:
            if lane["current_light"] == "green":
                # Turn red after green phase
                lane["current_light"] = "red"
                lane["time_remaining"] = random.randint(30, 60)
            elif lane["vehicle_count"] > 12:  # Prioritize congested lanes
                # Turn green if congested
                lane["current_light"] = "green"
                lane["time_remaining"] = lane["max_time"]
                # Turn other lanes red
                for other_id, other_lane in intersection_data["lanes"].items():
                    if other_id != lane_id and other_lane["current_light"] == "green":
                        other_lane["current_light"] = "red"
                        other_lane["time_remaining"] = random.randint(20, 40)
            else:
                # Stay red but reset timer
                lane["time_remaining"] = random.randint(15, 45)

async def create_websocket_message():
    """Create message using real ML data or fallback to simulated data"""
    global ml_traffic_data, last_ml_update
    
    # Try to fetch fresh ML data
    fresh_ml_data = await fetch_ml_data()
    if fresh_ml_data:
        return fresh_ml_data
    
    # Use cached ML data if available and recent (within last 30 seconds)
    if (ml_traffic_data is not None and 
        last_ml_update is not None and 
        (datetime.now() - last_ml_update).total_seconds() < 30):
        
        logger.info("Using cached ML data")
        return ml_traffic_data.dict()
    
    # Fallback to simulated data if no ML data available
    else:
        logger.info("No recent ML data available, using simulated data")
        
        # Determine current active phase (which directions have green light)
        green_directions = []
        current_phase_id = 0
        phase_status = "GREEN"
        remaining_time = 30
        
        for lane_id, lane in intersection_data["lanes"].items():
            if lane["current_light"] == "green":
                green_directions.append(lane["direction"])
                remaining_time = min(remaining_time, lane["time_remaining"])
        
        if not green_directions:
            phase_status = "RED"
            green_directions = ["none"]
            remaining_time = min(lane["time_remaining"] for lane in intersection_data["lanes"].values())
        
        # Calculate direction metrics
        direction_metrics = {}
        total_vehicles_passed = 0
        total_wait_time = 0
        direction_count = 0
        
        for direction in ["east", "west", "north", "south"]:
            # Find corresponding lane data
            lane_key = f"{direction[0]}-straight"
            lane = intersection_data["lanes"].get(lane_key, {})
            
            # Calculate vehicle type distribution
            total_vehicles = lane.get("vehicle_count", 0)
            car_count = int(total_vehicles * 0.7)
            bus_count = int(total_vehicles * 0.1)
            truck_count = int(total_vehicles * 0.1)
            bike_count = total_vehicles - car_count - bus_count - truck_count
            
            vehicles_crossed = random.randint(5, 15) if lane.get("current_light") == "green" else random.randint(0, 5)
            total_vehicles_passed += vehicles_crossed
            
            wait_time = lane.get("time_remaining", 25) + random.uniform(-5, 10)
            total_wait_time += wait_time
            direction_count += 1
            
        # Calculate environmental impact based on vehicle weight and consumption
        environmental_impact = calculate_environmental_impact(
            car_count, bus_count, truck_count, bike_count, 
            vehicles_crossed, wait_time, lane.get("current_light") == "green"
        )
        
        direction_metrics[direction] = {
            "vehicle_counts": {
                "car": car_count,
                "bus": bus_count,
                "truck": truck_count,
                "bike": bike_count
            },
            "queue_length": lane.get("queue_length", 0),
            "vehicles_crossed": vehicles_crossed,
            "avg_wait_time": round(wait_time, 1),
            "emergency_vehicle_present": random.choice([True, False]) if random.random() < 0.05 else False,
            "environmental_impact": environmental_impact
        }
        
        avg_wait_all_sides = total_wait_time / direction_count
        avg_speed = sum(lane["avg_speed"] for lane in intersection_data["lanes"].values()) / 4
        
        return {
            "simulation_id": "SIM_001",
            "timestamp": datetime.now().isoformat() + "Z",
            "intersection_id": "INT_001",
            "current_phase": {
                "phase_id": current_phase_id,
                "active_directions": green_directions,
                "status": phase_status,
                "remaining_time": remaining_time
            },
            "direction_metrics": direction_metrics,
            "overall_metrics": {
                "total_vehicles_passed": total_vehicles_passed,
                "avg_wait_time_all_sides": round(avg_wait_all_sides, 1),
                "throughput": round(total_vehicles_passed / 120, 2),  # vehicles per second in 2-minute cycle
                "avg_speed": round(avg_speed, 1),
                "cycle_time": 120
            }
        }

# WebSocket endpoint
@app.websocket("/ws/traffic")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        # Send initial data
        message = await create_websocket_message()
        await websocket.send_text(json.dumps(message))
        
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for client messages (like manual overrides)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                client_message = json.loads(data)
                
                # Handle manual signal override
                if client_message.get("type") == "manual_override":
                    lane_id = client_message.get("lane_id")
                    signal_state = client_message.get("signal_state") 
                    
                    if lane_id in intersection_data["lanes"]:
                        intersection_data["lanes"][lane_id]["current_light"] = signal_state
                        intersection_data["lanes"][lane_id]["time_remaining"] = 30
                        
                        # Send confirmation
                        await websocket.send_text(json.dumps({
                            "type": "override_confirmation",
                            "lane_id": lane_id,
                            "signal_state": signal_state,
                            "success": True
                        }))
                        
                        logger.info(f"Manual override: {lane_id} -> {signal_state}")
                        
            except asyncio.TimeoutError:
                # No message received, continue with regular updates
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Background task to broadcast updates
async def broadcast_updates():
    """Send real-time updates to all connected clients"""
    while True:
        if manager.active_connections:
            # Update the intersection data (simulate database changes)
            update_intersection_data()
            
            # Create and broadcast message using ML data
            message = await create_websocket_message()
            await manager.broadcast(json.dumps(message))
            
        # Wait 2 seconds before next update (as requested)
        await asyncio.sleep(2)

# Start background task when server starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_updates())
    logger.info("WebSocket broadcast service started")

# Health endpoint
@app.get("/health")
def health_check():
    ml_status = "available" if ml_traffic_data else "unavailable"
    last_update_str = last_ml_update.isoformat() if last_ml_update else "never"
    
    return {
        "status": "healthy",
        "ml_data_status": ml_status,
        "last_ml_update": last_update_str,
        "ml_api_endpoint": ML_INGEST_ENDPOINT,
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

# Debug endpoint to get current ML data
@app.get("/debug/ml-data")
async def get_current_ml_data():
    """Get current ML data for debugging"""
    fresh_data = await fetch_ml_data()
    return {
        "fresh_data": fresh_data,
        "cached_data": ml_traffic_data.dict() if ml_traffic_data else None,
        "last_update": last_ml_update.isoformat() if last_ml_update else None,
        "ml_endpoint": ML_INGEST_ENDPOINT
    }

# Endpoint to manually trigger ML data fetch
@app.post("/debug/fetch-ml-data")
async def manual_fetch_ml_data():
    """Manually trigger ML data fetch for testing"""
    result = await fetch_ml_data()
    if result:
        return {"success": True, "data": result}
    else:
        return {"success": False, "message": "Failed to fetch ML data"}

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await httpx_client.aclose()
    logger.info("HTTP client closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)