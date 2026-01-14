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
from database import get_db, db_manager
from ingestion import ingestion_service, SimulationDataModel
from analytics import analytics_service
from models import Base

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
        # The logic below is the corrected version that was previously misplaced.
        # It's now properly inside a function and correctly calls the ingestion service.
        result = ingestion_service.ingest_simulation_data(request.data)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "message": "Data ingested successfully",
            "result": result
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
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("Starting Smart Traffic Analytics API...")
    try:
        # Ensure database tables exist
        db_manager.create_tables()
        logger.info("Database tables verified/created")
        
        # Any other startup tasks
        logger.info("API startup completed successfully")
    
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Smart Traffic Analytics API...")
    # Add any cleanup tasks here
    logger.info("Shutdown completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # For development
        log_level="info"
    )

@app.post("/api/v1/ingest/batch")
async def batch_ingest_simulation_data(request: BatchIngestRequest):
    """
    Batch ingest multiple simulation data points for better performance.
    """
    try:
        # Convert dict data to JSON strings for the ingestion service
        json_data_list = [json.dumps(data) for data in request.data_list]
        
        result = await ingestion_service.batch_ingest(json_data_list)
        
        return {
            "message": "Batch ingestion completed",
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Batch ingestion error: {e}")
        raise HTTPException(status_code=400, detail=f"Batch ingestion failed: {str(e)}")

# Analytics endpoints
@app.get("/api/v1/analytics/simulation/{simulation_id}/summary")
async def get_simulation_summary(simulation_id: str):
    """Get comprehensive summary for a specific simulation."""
    try:
        result = await analytics_service.get_simulation_summary(simulation_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary error: {e}")
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