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
from .database import get_db, db_manager
from .ingestion import ingestion_service, SimulationDataModel
from .analytics import analytics_service
from .models import Base

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
        db_healthy = await db_manager.health_check()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "traffic-analytics-api"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/system/info")
async def system_info():
    """Get system information and connection stats."""
    try:
        connection_info = db_manager.get_connection_info()
        return {
            "database": connection_info,
            "service_info": {
                "name": "Smart Traffic Analytics API",
                "version": "1.0.0",
                "uptime": "N/A"  # Would implement actual uptime tracking
            }
        }
    except Exception as e:
        logger.error(f"System info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data ingestion endpoints
@app.post("/api/v1/ingest/simulation")
async def ingest_simulation_data(request: SimulationIngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest single simulation data point.
    Processes in background for better response times.
    """
    try:
        # Validate the data structure
        simulation_data = SimulationDataModel(**request.data)
        
        # Process ingestion
        result = await ingestion_service.ingest_simulation_data(request.data)
        return result
    
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ingest/batch")
async def batch_ingest_simulation_data(request: BatchIngestRequest, background_tasks: BackgroundTasks):
    """
    Batch ingest multiple simulation data points for better performance.
    """
    try:
        result = await ingestion_service.batch_ingest(request.data_list)
        return result
    
    except Exception as e:
        logger.error(f"Batch ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/api/v1/analytics/wait-times")
async def get_wait_time_analytics(
    simulation_id: Optional[str] = Query(None),
    intersection_id: Optional[str] = Query(None), 
    time_window_hours: Optional[int] = Query(None)
):
    """Get average wait time analytics with filtering options."""
    try:
        result = await analytics_service.get_average_wait_times(
            simulation_id=simulation_id,
            intersection_id=intersection_id,
            time_window_hours=time_window_hours
        )
        return result
    
    except Exception as e:
        logger.error(f"Wait time analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/comparison/baseline-vs-ai")
async def get_baseline_ai_comparison(
    intersection_id: Optional[str] = Query(None),
    time_window_hours: Optional[int] = Query(24),
    metric: str = Query("wait_time")
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
        logger.error(f"Comparison analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/environmental-impact")
async def get_environmental_impact(
    simulation_id: Optional[str] = Query(None),
    comparison_mode: bool = Query(False)
):
    """Get environmental impact analysis including fuel and CO2 savings."""
    try:
        result = await analytics_service.get_environmental_impact(
            simulation_id=simulation_id,
            comparison_mode=comparison_mode
        )
        return result
    
    except Exception as e:
        logger.error(f"Environmental impact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/emergency-handling")
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
        # Get recent metrics across all active simulations
        wait_times = await analytics_service.get_average_wait_times(time_window_hours=1)
        speeds = await analytics_service.get_average_speeds()
        environmental = await analytics_service.get_environmental_impact()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "wait_times": wait_times,
            "speeds": speeds,
            "environmental_impact": environmental
        }
    
    except Exception as e:
        logger.error(f"Live metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
async def get_performance_scatter_data(
    metric_x: str = Query("avg_wait_time"),
    metric_y: str = Query("throughput"),
    time_window_hours: int = Query(24)
):
    """Get performance scatter plot data for comparison visualization."""
    try:
        comparison_data = await analytics_service.get_baseline_vs_ai_comparison(
            time_window_hours=time_window_hours
        )
        
        scatter_data = []
        for mode, data in comparison_data["comparison_data"].items():
            scatter_data.append({
                "mode": mode,
                "x": data.get(metric_x, 0),
                "y": data.get(metric_y, 0),
                "data_points": data.get("data_points", 0)
            })
        
        return {
            "chart_type": "scatter",
            "x_axis": metric_x,
            "y_axis": metric_y,
            "data": scatter_data,
            "improvements": comparison_data.get("improvements", {})
        }
    
    except Exception as e:
        logger.error(f"Scatter plot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Simulation management endpoints
@app.get("/api/v1/simulations/{simulation_id}")
async def get_simulation_summary(simulation_id: str):
    """Get comprehensive summary for a specific simulation."""
    try:
        result = await analytics_service.get_simulation_summary(simulation_id)
        return result
    
    except Exception as e:
        logger.error(f"Simulation summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting Traffic Analytics API...")
    # Create database tables if they don't exist
    try:
        db_manager.create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Smart Traffic Signal Analytics API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "documentation": "/docs",
            "health_check": "/health",
            "system_info": "/system/info"
        }
    }
