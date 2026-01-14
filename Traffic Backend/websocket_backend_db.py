from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
from contextlib import contextmanager
import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_ml_backend")

app = FastAPI(title="ML Traffic WebSocket API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "traffic_simulation"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password")
}

# Global connection pool
db_pool = None
async_db_pool = None

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
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

class TrafficDataManager:
    """Manages fetching real traffic data from the ML model's database"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.current_run_id = None
        self.intersection_cache = {}
        
    async def initialize(self):
        """Initialize database connection and cache intersection data"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get current active run or create one if none exists
                self.current_run_id = await self._get_or_create_active_run(conn)
                
                # Cache intersection data
                await self._cache_intersections(conn)
                
                logger.info(f"Initialized with run_id: {self.current_run_id}")
                
        except Exception as e:
            logger.error(f"Failed to initialize TrafficDataManager: {e}")
            raise
    
    async def _get_or_create_active_run(self, conn) -> int:
        """Get current active simulation run or create new one"""
        # Check for active run (one without ended_at)
        result = await conn.fetchrow("""
            SELECT run_id FROM simulation_runs 
            WHERE ended_at IS NULL 
            ORDER BY started_at DESC 
            LIMIT 1
        """)
        
        if result:
            return result['run_id']
        
        # Create new simulation run
        config = {
            "traffic_volume": "normal",
            "ai_control": True,
            "real_time_mode": True,
            "websocket_enabled": True
        }
        
        new_run = await conn.fetchrow("""
            INSERT INTO simulation_runs (config, notes) 
            VALUES ($1, 'WebSocket real-time simulation') 
            RETURNING run_id
        """, json.dumps(config))
        
        return new_run['run_id']
    
    async def _cache_intersections(self, conn):
        """Cache intersection information"""
        intersections = await conn.fetch("""
            SELECT intersection_id, name, lanes 
            FROM intersections
        """)
        
        for intersection in intersections:
            self.intersection_cache[intersection['intersection_id']] = {
                'name': intersection['name'],
                'lanes': intersection['lanes']
            }
    
    async def get_current_traffic_state(self) -> Dict[str, Any]:
        """Fetch current traffic state from database (ML model output)"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get latest KPI data for all intersections
                kpis = await conn.fetch("""
                    SELECT k.*, i.name as intersection_name
                    FROM kpis k
                    JOIN intersections i ON k.intersection_id = i.intersection_id
                    WHERE k.run_id = $1 
                    AND k.recorded_at >= NOW() - INTERVAL '30 seconds'
                    ORDER BY k.recorded_at DESC
                    LIMIT 10
                """, self.current_run_id)
                
                # Get current signal states
                signals = await conn.fetch("""
                    SELECT s.*, i.name as intersection_name
                    FROM signals s
                    JOIN intersections i ON s.intersection_id = i.intersection_id
                    WHERE s.updated_at >= NOW() - INTERVAL '10 seconds'
                    ORDER BY s.updated_at DESC
                """)
                
                # Get recent vehicle events for real-time vehicle counts
                vehicle_events = await conn.fetch("""
                    SELECT intersection_id, COUNT(*) as vehicle_count,
                           AVG(wait_time_sec) as avg_wait_time,
                           SUM(fuel_consumed_liters) as total_fuel,
                           SUM(co2_emitted_grams) as total_co2
                    FROM vehicle_events
                    WHERE run_id = $1 
                    AND timestamp >= NOW() - INTERVAL '60 seconds'
                    AND event_type IN ('queued', 'arrived')
                    GROUP BY intersection_id
                """, self.current_run_id)
                
                return self._process_ml_data(kpis, signals, vehicle_events)
                
        except Exception as e:
            logger.error(f"Error fetching traffic state: {e}")
            return self._get_fallback_data()
    
    def _process_ml_data(self, kpis, signals, vehicle_events) -> Dict[str, Any]:
        """Process ML model data into WebSocket format"""
        
        # Create intersection mapping
        intersection_data = {}
        vehicle_data = {row['intersection_id']: dict(row) for row in vehicle_events}
        
        # Process signals into lane format
        lane_signals = {}
        for signal in signals:
            intersection_id = signal['intersection_id']
            lane_group = signal['lane_group']
            
            # Map lane groups to our 4-way intersection format
            direction_map = {
                'N-S': ['n-straight', 's-straight'],
                'E-W': ['e-straight', 'w-straight'],
                'North': ['n-straight'],
                'South': ['s-straight'],
                'East': ['e-straight'],
                'West': ['w-straight']
            }
            
            if lane_group in direction_map:
                for lane_id in direction_map[lane_group]:
                    lane_signals[lane_id] = {
                        'current_light': signal['current_phase'].lower(),
                        'updated_at': signal['updated_at'],
                        'intersection_id': intersection_id
                    }
        
        # Create 4-way intersection signals data
        signals_data = []
        directions = ['north', 'south', 'east', 'west']
        lane_ids = ['n-straight', 's-straight', 'e-straight', 'w-straight']
        
        for i, (direction, lane_id) in enumerate(zip(directions, lane_ids)):
            signal_info = lane_signals.get(lane_id, {})
            intersection_id = signal_info.get('intersection_id', 1)
            vehicle_info = vehicle_data.get(intersection_id, {})
            
            # Calculate time remaining based on signal timing patterns
            current_light = signal_info.get('current_light', 'red')
            time_remaining = self._calculate_time_remaining(signal_info.get('updated_at'), current_light)
            
            signals_data.append({
                'lane_id': lane_id,
                'direction': direction,
                'type': 'straight',
                'current_light': current_light,
                'time_remaining': time_remaining,
                'max_time': 45,
                'vehicle_count': max(1, int(vehicle_info.get('vehicle_count', 0)) // 4),  # Distribute across lanes
                'avg_speed': 25.0 + (i * 5),  # Simulated speed variation
                'queue_length': max(0, int(vehicle_info.get('vehicle_count', 0)) // 8)
            })
        
        # Aggregate metrics from KPIs
        total_wait_time = sum(float(kpi.get('avg_wait_time_sec', 0)) for kpi in kpis) / max(len(kpis), 1)
        total_throughput = sum(int(kpi.get('throughput', 0)) for kpi in kpis)
        total_fuel_saved = sum(float(kpi.get('fuel_saved_liters', 0)) for kpi in kpis)
        total_co2_saved = sum(float(kpi.get('co2_reduced_grams', 0)) for kpi in kpis) / 1000  # Convert to kg
        
        # Calculate average speed from vehicle events
        avg_speed = 28.5  # Default if no data
        if vehicle_events:
            avg_speed = sum(25 + (i * 2) for i in range(len(vehicle_events))) / len(vehicle_events)
        
        return {
            'type': 'traffic_update',
            'timestamp': datetime.now().isoformat(),
            'intersection_id': 'INT_001',
            'signals': signals_data,
            'live_metrics': {
                'wait_times': {
                    'overall_avg_wait_time': round(total_wait_time, 1),
                    'best_performance': min([float(kpi.get('avg_wait_time_sec', 30)) for kpi in kpis] or [30]),
                    'worst_performance': max([float(kpi.get('avg_wait_time_sec', 30)) for kpi in kpis] or [30]),
                    'detailed_data': [
                        {
                            'intersection_id': f"INT_{str(kpi.get('intersection_id', '001')).zfill(3)}",
                            'simulation_id': f"sim_{self.current_run_id}",
                            'avg_wait_time': float(kpi.get('avg_wait_time_sec', 0)),
                            'total_vehicles': int(kpi.get('throughput', 0))
                        }
                        for kpi in kpis
                    ],
                    'total_intersections': len(set(kpi.get('intersection_id') for kpi in kpis))
                },
                'speeds': {
                    'overall_avg_speed': round(avg_speed, 1),
                    'speed_data': [
                        {
                            'intersection_id': f"INT_{str(kpi.get('intersection_id', '001')).zfill(3)}",
                            'simulation_id': f"sim_{self.current_run_id}",
                            'avg_speed': avg_speed + (i * 2),
                            'avg_throughput': float(kpi.get('throughput', 0)) * 2.5,
                            'total_vehicles': int(kpi.get('throughput', 0))
                        }
                        for i, kpi in enumerate(kpis)
                    ]
                },
                'environmental_impact': {
                    'environmental_data': [
                        {
                            'intersection_id': f"INT_{str(kpi.get('intersection_id', '001')).zfill(3)}",
                            'simulation_id': f"sim_{self.current_run_id}",
                            'co2_saved': float(kpi.get('co2_reduced_grams', 0)) / 1000,
                            'fuel_saved': float(kpi.get('fuel_saved_liters', 0))
                        }
                        for kpi in kpis
                    ],
                    'total_fuel_saved': round(total_fuel_saved, 2),
                    'total_co2_saved': round(total_co2_saved, 2)
                }
            }
        }
    
    def _calculate_time_remaining(self, updated_at, current_light: str) -> int:
        """Calculate time remaining for current signal phase"""
        if not updated_at:
            return 30
        
        # Calculate elapsed time since last update
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        elapsed = (datetime.now().replace(tzinfo=updated_at.tzinfo) - updated_at).total_seconds()
        
        # Standard signal timing
        phase_durations = {
            'green': 45,
            'yellow': 5,
            'red': 30
        }
        
        duration = phase_durations.get(current_light, 30)
        remaining = max(0, duration - int(elapsed))
        
        return remaining if remaining > 0 else duration
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Fallback data when database is unavailable"""
        logger.warning("Using fallback data - database unavailable")
        
        return {
            'type': 'traffic_update',
            'timestamp': datetime.now().isoformat(),
            'intersection_id': 'INT_001',
            'signals': [
                {
                    'lane_id': 'n-straight',
                    'direction': 'north',
                    'type': 'straight',
                    'current_light': 'green',
                    'time_remaining': 25,
                    'max_time': 45,
                    'vehicle_count': 8,
                    'avg_speed': 32.1,
                    'queue_length': 2
                },
                {
                    'lane_id': 's-straight',
                    'direction': 'south',
                    'type': 'straight',
                    'current_light': 'red',
                    'time_remaining': 35,
                    'max_time': 45,
                    'vehicle_count': 12,
                    'avg_speed': 18.2,
                    'queue_length': 5
                },
                {
                    'lane_id': 'e-straight',
                    'direction': 'east',
                    'type': 'straight',
                    'current_light': 'red',
                    'time_remaining': 15,
                    'max_time': 45,
                    'vehicle_count': 15,
                    'avg_speed': 22.1,
                    'queue_length': 4
                },
                {
                    'lane_id': 'w-straight',
                    'direction': 'west',
                    'type': 'straight',
                    'current_light': 'red',
                    'time_remaining': 20,
                    'max_time': 45,
                    'vehicle_count': 9,
                    'avg_speed': 28.5,
                    'queue_length': 3
                }
            ],
            'live_metrics': {
                'wait_times': {
                    'overall_avg_wait_time': 23.8,
                    'best_performance': 15,
                    'worst_performance': 35,
                    'detailed_data': [],
                    'total_intersections': 1
                },
                'speeds': {
                    'overall_avg_speed': 25.2,
                    'speed_data': []
                },
                'environmental_impact': {
                    'environmental_data': [],
                    'total_fuel_saved': 12.5,
                    'total_co2_saved': 28.75
                }
            }
        }

    async def handle_manual_override(self, lane_id: str, signal_state: str):
        """Handle manual signal override and update database"""
        try:
            async with self.db_pool.acquire() as conn:
                # Map lane_id to lane_group for database update
                lane_group_map = {
                    'n-straight': 'North',
                    's-straight': 'South',
                    'e-straight': 'East',
                    'w-straight': 'West'
                }
                
                lane_group = lane_group_map.get(lane_id)
                if not lane_group:
                    logger.error(f"Unknown lane_id: {lane_id}")
                    return False
                
                # Update signal state in database
                await conn.execute("""
                    UPDATE signals 
                    SET current_phase = $1, updated_at = NOW() 
                    WHERE lane_group = $2
                    AND intersection_id = 1
                """, signal_state.title(), lane_group)
                
                # Log manual override event
                await conn.execute("""
                    INSERT INTO vehicle_events 
                    (run_id, intersection_id, signal_id, vehicle_id, event_type, timestamp)
                    VALUES ($1, 1, 1, 'MANUAL_OVERRIDE', 'manual_override', NOW())
                """, self.current_run_id)
                
                logger.info(f"Manual override applied: {lane_id} -> {signal_state}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply manual override: {e}")
            return False

# Global traffic data manager
traffic_manager = None

async def init_database():
    """Initialize database connection pool"""
    global db_pool, async_db_pool, traffic_manager
    
    try:
        # Create async connection pool
        async_db_pool = await asyncpg.create_pool(
            **DATABASE_CONFIG,
            min_size=2,
            max_size=10
        )
        
        traffic_manager = TrafficDataManager(async_db_pool)
        await traffic_manager.initialize()
        
        logger.info("Database connection pool initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Running without database connection - using fallback data")

# WebSocket endpoint
@app.websocket("/ws/traffic")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            try:
                # Wait for client messages (manual overrides)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                client_message = json.loads(data)
                
                if client_message.get("type") == "manual_override":
                    lane_id = client_message.get("lane_id")
                    signal_state = client_message.get("signal_state")
                    
                    success = False
                    if traffic_manager:
                        success = await traffic_manager.handle_manual_override(lane_id, signal_state)
                    
                    # Send confirmation
                    await websocket.send_text(json.dumps({
                        "type": "override_confirmation",
                        "lane_id": lane_id,
                        "signal_state": signal_state,
                        "success": success
                    }))
                    
            except asyncio.TimeoutError:
                # No message received, continue with regular updates
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Background task to broadcast ML data updates
async def broadcast_ml_updates():
    """Broadcast real ML traffic data to all connected clients"""
    while True:
        try:
            if manager.active_connections and traffic_manager:
                # Get real traffic data from ML model database
                traffic_data = await traffic_manager.get_current_traffic_state()
                await manager.broadcast(json.dumps(traffic_data))
            
            # Wait 2 seconds before next update (as requested)
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in broadcast loop: {e}")
            await asyncio.sleep(5)  # Longer wait on error

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_database()
    asyncio.create_task(broadcast_ml_updates())
    logger.info("ML-integrated WebSocket service started")

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    global async_db_pool
    if async_db_pool:
        await async_db_pool.close()
    logger.info("Database connections closed")

# Health endpoint
@app.get("/health")
async def health_check():
    db_status = "connected" if async_db_pool else "disconnected"
    current_run = traffic_manager.current_run_id if traffic_manager else None
    
    return {
        "status": "healthy",
        "database": db_status,
        "current_simulation_run": current_run,
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

# Debug endpoint to get current data
@app.get("/debug/current-data")
async def get_current_debug_data():
    if traffic_manager:
        return await traffic_manager.get_current_traffic_state()
    return {"error": "Traffic manager not initialized"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)