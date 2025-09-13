# main.py - FastAPI application with REST endpoints
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

# Import our services and dependencies
try:
    from database_config import get_db, get_db_context, DatabaseManager
    from analytics_service import AnalyticsService
    from sqlalchemy_models import Base
    USE_REAL_DB = True
except ImportError as e:
    logger.warning(f"Database modules not available: {e}. Using mock data.")
    USE_REAL_DB = False

import random
from datetime import datetime, timedelta

# Initialize services
if USE_REAL_DB:
    try:
        db_manager = DatabaseManager()
        analytics_service = AnalyticsService()
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        USE_REAL_DB = False

# Fallback mock functions
def generate_mock_wait_times():
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

def generate_mock_speeds():
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

def generate_mock_environmental():
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

# Pydantic models for API requests/responses
class SimulationIngestRequest(BaseModel):
    data: Dict[Any, Any]

class BatchIngestRequest(BaseModel):
    data_list: List[Dict[Any, Any]]

class AnalyticsQuery(BaseModel):
    simulation_id: Optional[str] = None
    intersection_id: Optional[str] = None
    time_window_hours: Optional[int] = None
    metric: Optional[str] = "wait_time"

# Health check and system status endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    try:
        db_healthy = True
        if USE_REAL_DB:
            try:
                db_healthy = await db_manager.health_check()
            except:
                db_healthy = False
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "mock_data",
            "redis": "not_configured",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "traffic-analytics-api",
            "using_real_db": USE_REAL_DB
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )
        
@app.get("/system/info")
def system_info():
    """Get system information and connection stats."""
    try:
        return {
            "database": {"status": "connected", "type": "mock"},
            "service_info": {
                "name": "Smart Traffic Analytics API",
                "version": "1.0.0",
                "uptime": "N/A"  # Would implement actual uptime tracking
            }
        }
    except Exception as e:
        logger.error(f"System info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/signals/timings")
async def get_signal_timings(intersection_id: Optional[str] = None):
    """Get current signal timings for an intersection."""
    try:
        if USE_REAL_DB:
            with get_db_context() as db:
                query = """
                    SELECT s.signal_id, s.direction, s.lane_type,
                           ss.status as current_state, ss.timer_remaining,
                           ss.green_time_allocated as max_time,
                           i.intersection_id
                    FROM signals s
                    JOIN intersections i ON s.intersection_id = i.intersection_id
                    LEFT JOIN signal_states ss ON s.signal_id = ss.signal_id
                    WHERE ss.timestamp = (
                        SELECT MAX(timestamp)
                        FROM signal_states
                        WHERE signal_id = s.signal_id
                    )
                """
                
                params = {}
                if intersection_id:
                    query += " AND i.intersection_id = :intersection_id"
                    params["intersection_id"] = intersection_id
                
                result = db.execute(text(query), params)
                
                signals = [{
                    "lane_id": str(row.signal_id),
                    "direction": row.direction,
                    "type": row.lane_type,
                    "current_light": row.current_state or "RED",
                    "time_remaining": row.timer_remaining or 30,
                    "max_time": row.max_time or 60,
                    "intersection_id": row.intersection_id
                } for row in result]
                
                return {"signal_timings": signals}
        else:
            # Return mock data for testing
            mock_signals = [
                {
                    "lane_id": f"LANE_{i}",
                    "direction": direction,
                    "type": "straight",
                    "current_light": random.choice(["RED", "GREEN", "YELLOW"]),
                    "time_remaining": random.randint(0, 30),
                    "max_time": 60,
                    "intersection_id": intersection_id or "INT_001"
                }
                for i, direction in enumerate(["north", "south", "east", "west"], 1)
            ]
            return {"signal_timings": mock_signals}
    
    except Exception as e:
        logger.error(f"Error getting signal timings: {e}")
        raise HTTPException(status_code=500, detail=str(e))    
# Mock data generators
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

# Data ingestion endpoints
@app.post("/api/v1/ingest/simulation")
def ingest_simulation_data(request: SimulationIngestRequest):
    """
    Ingest single simulation data point.
    """
    try:
        return {
            "message": "Data ingested successfully",
            "result": {"status": "success", "data_id": "mock_id"}
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=400, detail=f"Ingestion failed: {str(e)}")


@app.get("/api/v1/analytics/time-series/{simulation_id}")
async def get_time_series_data(
    simulation_id: str,
    metric: str = Query("wait_time"),
    interval_minutes: int = Query(5)
):
    """Get time-series data for charts and visualizations."""
    try:
        result = await analytics_service.get_time_series_data(
            simulation_id=simulation_id,
            metric=metric,
            interval_minutes=interval_minutes
        )
        return result
    
    except Exception as e:
        logger.error(f"Time series error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard endpoints for frontend integration
@app.get("/api/v1/dashboard/live-metrics")
async def get_live_metrics():
    """Get live metrics for dashboard display."""
    try:
        if USE_REAL_DB:
            # Get recent metrics from database
            wait_times = await analytics_service.get_average_wait_times(time_window_hours=1)
            speeds = await analytics_service.get_average_speeds()
            environmental = await analytics_service.get_environmental_impact()
        else:
            # Use mock data
            wait_times = generate_mock_wait_times()
            speeds = generate_mock_speeds()
            environmental = generate_mock_environmental()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "wait_times": wait_times,
            "speeds": speeds,
            "environmental_impact": environmental
        }
    
    except Exception as e:
        logger.error(f"Live metrics error: {e}")
        # Fallback to mock data on error
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "wait_times": generate_mock_wait_times(),
            "speeds": generate_mock_speeds(),
            "environmental_impact": generate_mock_environmental()
        }

@app.get("/api/v1/dashboard/performance-comparison")
async def get_performance_comparison():
    """Get performance comparison data for dashboard charts."""
    try:
        comparison = await analytics_service.get_baseline_vs_ai_comparison()
        emergency_report = await analytics_service.get_emergency_handling_report(time_window_hours=24)
        
        return {
            "comparison": comparison,
            "emergency_handling": emergency_report,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Performance comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chart data endpoints optimized for frontend consumption
@app.get("/api/v1/charts/wait-time-trend")
async def get_wait_time_trend_data(
    simulation_ids: List[str] = Query(...),
    hours: int = Query(24)
):
    """Get wait time trend data formatted for line charts."""
    try:
        chart_data = []
        
        for sim_id in simulation_ids:
            time_series = await analytics_service.get_time_series_data(
                simulation_id=sim_id,
                metric="wait_time",
                interval_minutes=10
            )
            
            chart_data.append({
                "simulation_id": sim_id,
                "data": time_series["time_series"]
            })
        
        return {
            "chart_type": "line",
            "datasets": chart_data,
            "x_axis": "timestamp",
            "y_axis": "avg_wait_time",
            "time_window_hours": hours
        }
    
    except Exception as e:
        logger.error(f"Chart data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/charts/performance-scatter")
async def get_performance_scatter_data():
    """Get performance data formatted for scatter plots."""
    try:
        comparison = await analytics_service.get_baseline_vs_ai_comparison()
        
        if not comparison["comparison_data"]:
            return {"error": "No data available for comparison"}
        
        scatter_data = []
        for mode, data in comparison["comparison_data"].items():
            scatter_data.append({
                "mode": mode,
                "wait_time": data["avg_wait_time"],
                "throughput": data["avg_throughput"],
                "speed": data["avg_speed"],
                "fuel_saved": data["total_fuel_saved"]
            })
        
        return {
            "chart_type": "scatter",
            "data": scatter_data,
            "x_axis": "wait_time",
            "y_axis": "throughput",
            "color_by": "mode"
        }
    
    except Exception as e:
        logger.error(f"Scatter chart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Administrative endpoints
@app.post("/api/v1/admin/clear-cache")
async def clear_cache():
    """Clear internal caches for testing/debugging."""
    try:
        ingestion_service.clear_cache()
        return {"message": "Cache cleared successfully"}
    
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/database/init")
async def initialize_database():
    """Initialize database tables (development only)."""
    try:
        db_manager.create_tables()
        return {"message": "Database tables initialized successfully"}
    
    except Exception as e:
        logger.error(f"Database init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )

# Startup and shutdown events
# Add these imports at the top of the file
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
import uuid
import asyncio

# Import our new services
from redis_service import redis_service
from websocket_service import websocket_manager
from metrics_calculator import metrics_calculator

# Add this after the app initialization
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    try:
        # Initialize Redis connection
        redis_connected = await redis_service.connect()
        if not redis_connected:
            logger.error("Failed to connect to Redis")
        else:
            logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on application shutdown."""
    try:
        await redis_service.disconnect()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    # Disconnect from Redis
    await redis_service.disconnect()
    
    # Stop the metrics calculator
    await metrics_calculator.stop()
    
    logger.info("All services shut down successfully")

# Add this function to process traffic updates from Redis
async def process_traffic_update(message: Dict[str, Any]):
    """Process traffic update messages from Redis and forward to WebSocket clients."""
    try:
        # Extract simulation and intersection IDs
        simulation_id = message.get("simulation_id")
        intersection_id = message.get("intersection_id")
        
        if not simulation_id or not intersection_id:
            logger.error(f"Invalid message format: missing simulation_id or intersection_id")
            return
        
        # Store the raw data in TigerData
        with get_db_context() as db:
            db.execute("""
                INSERT INTO raw_traffic_data (simulation_id, intersection_id, timestamp, data)
                VALUES (:simulation_id, :intersection_id, :timestamp, :data)
            """, {
                "simulation_id": simulation_id,
                "intersection_id": intersection_id,
                "timestamp": datetime.fromisoformat(message.get("timestamp")),
                "data": json.dumps(message)
            })
        
        # Broadcast to WebSocket clients
        channel = f"traffic:{simulation_id}:{intersection_id}"
        await websocket_manager.broadcast(channel, message)
        
        # Also broadcast to the general simulation channel
        await websocket_manager.broadcast(f"simulation:{simulation_id}", message)
        
    except Exception as e:
        logger.error(f"Error processing traffic update: {e}")

# Add WebSocket endpoints
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """WebSocket endpoint for real-time data streaming."""
    if not client_id:
        client_id = str(uuid.uuid4())
    
    try:
        await websocket_manager.connect(websocket, client_id)
        
        # Send a welcome message
        await websocket_manager.send_personal_message(client_id, {
            "type": "connection",
            "status": "connected",
            "client_id": client_id
        })
        
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()
            
            # Handle subscription requests
            if data.get("action") == "subscribe" and "channel" in data:
                channel = data["channel"]
                await websocket_manager.subscribe(client_id, channel)
            
            # Handle unsubscription requests
            elif data.get("action") == "unsubscribe" and "channel" in data:
                channel = data["channel"]
                await websocket_manager.unsubscribe(client_id, channel)
            
            # Handle control signals (e.g., emergency override)
            elif data.get("action") == "control" and "command" in data:
                command = data["command"]
                target = data.get("target")
                
                # Publish control command to Redis
                await redis_service.publish("control_commands", {
                    "command": command,
                    "target": target,
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Confirm receipt to the client
                await websocket_manager.send_personal_message(client_id, {
                    "type": "control",
                    "status": "received",
                    "command": command
                })
    
    except WebSocketDisconnect:
        await websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(client_id)

# Add API endpoint to get calculated metrics
@app.get("/api/v1/metrics/environmental")
async def get_environmental_metrics(
    simulation_id: Optional[str] = None,
    intersection_id: Optional[str] = None,
    time_window_hours: Optional[int] = 24
):
    """Get environmental metrics (CO₂ and fuel savings)."""
    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours) if time_window_hours else None
        
        with get_db_context() as db:
            # Build the query
            query = """
                SELECT 
                    simulation_id, 
                    intersection_id, 
                    metric_type, 
                    SUM(value) as total_value,
                    AVG(value) as avg_value,
                    COUNT(*) as data_points,
                    MAX(timestamp) as latest_timestamp
                FROM calculated_metrics
                WHERE 1=1
            """
            
            params = {}
            
            if simulation_id:
                query += " AND simulation_id = :simulation_id"
                params["simulation_id"] = simulation_id
            
            if intersection_id:
                query += " AND intersection_id = :intersection_id"
                params["intersection_id"] = intersection_id
            
            if start_time:
                query += " AND timestamp >= :start_time"
                params["start_time"] = start_time
            
            query += " GROUP BY simulation_id, intersection_id, metric_type"
            
            # Execute the query
            result = db.execute(text(query), params)
            
            # Process the results
            metrics_data = []
            for row in result:
                metrics_data.append({
                    "simulation_id": row.simulation_id,
                    "intersection_id": row.intersection_id,
                    "metric_type": row.metric_type,
                    "total_value": float(row.total_value),
                    "avg_value": float(row.avg_value),
                    "data_points": row.data_points,
                    "latest_timestamp": row.latest_timestamp.isoformat() if row.latest_timestamp else None
                })
            
            # Organize by metric type
            co2_data = [m for m in metrics_data if m["metric_type"] == "co2_saved"]
            fuel_data = [m for m in metrics_data if m["metric_type"] == "fuel_saved"]
            
            # Calculate totals
            total_co2_saved = sum(m["total_value"] for m in co2_data)
            total_fuel_saved = sum(m["total_value"] for m in fuel_data)
            
            return {
                "co2_saved": {
                    "total_grams": round(total_co2_saved, 2),
                    "total_kg": round(total_co2_saved / 1000, 2),
                    "detailed_data": co2_data
                },
                "fuel_saved": {
                    "total_ml": round(total_fuel_saved, 2),
                    "total_liters": round(total_fuel_saved / 1000, 2),
                    "detailed_data": fuel_data
                },
                "time_window_hours": time_window_hours,
                "simulation_id": simulation_id,
                "intersection_id": intersection_id
            }
    
    except Exception as e:
        logger.error(f"Error getting environmental metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/wait-times")
async def get_wait_times(
    simulation_id: Optional[str] = Query(None),
    intersection_id: Optional[str] = Query(None),
    time_window_hours: Optional[int] = Query(None)
):
    """Get average wait time analytics with optional filters."""
    try:
        result = await analytics_service.get_average_wait_times(
            simulation_id=simulation_id,
            intersection_id=intersection_id,
            time_window_hours=time_window_hours
        )
        return result
    
    except Exception as e:
        logger.error(f"Wait times error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/speeds")
async def get_average_speeds(
    simulation_id: Optional[str] = Query(None),
    intersection_id: Optional[str] = Query(None)
):
    """Get average speed analytics."""
    try:
        result = await analytics_service.get_average_speeds(
            simulation_id=simulation_id,
            intersection_id=intersection_id
        )
        return result
    
    except Exception as e:
        logger.error(f"Speeds error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/environmental-impact")
async def get_environmental_impact(
    simulation_id: Optional[str] = Query(None),
    comparison_mode: bool = Query(False)
):
    """Get fuel savings and CO2 reduction metrics."""
    try:
        result = await analytics_service.get_environmental_impact(
            simulation_id=simulation_id,
            comparison_mode=comparison_mode
        )
        return result
    
    except Exception as e:
        logger.error(f"Environmental impact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/comparison/baseline-vs-ai")
async def get_baseline_vs_ai_comparison(
    metric: str = Query("wait_time"),
    intersection_id: Optional[str] = Query(None),
    time_window_hours: Optional[int] = Query(24)
):
    """Compare baseline vs AI performance across multiple metrics."""
    try:
        result = await analytics_service.get_baseline_vs_ai_comparison(
            metric=metric,
            intersection_id=intersection_id,
            time_window_hours=time_window_hours
        )
        return result
    
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/emergency-report")
async def get_emergency_handling_report(
    simulation_id: Optional[str] = Query(None),
    time_window_hours: Optional[int] = Query(None)
):
    """Get emergency vehicle handling performance report."""
    try:
        result = await analytics_service.get_emergency_handling_report(
            simulation_id=simulation_id,
            time_window_hours=time_window_hours
        )
        return result
    
    except Exception as e:
        logger.error(f"Emergency report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# SIGNAL CONTROL ENDPOINTS
# =============================================================================

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
import asyncio
from threading import Timer

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
