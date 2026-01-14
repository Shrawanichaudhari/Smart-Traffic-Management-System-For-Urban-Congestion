# ingestion.py - Data ingestion service for simulation JSON data
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import json
from pydantic import BaseModel, Field, validator
from models import (
    Simulation, SignalState, TrafficData, PerformanceMetric, 
    EmergencyEvent, Signal, Intersection
)
from database import get_db_context

# Pydantic models for JSON validation
class VehicleCountsModel(BaseModel):
    car: int = 0
    bus: int = 0
    truck: int = 0
    bike: int = 0
    rickshaw: int = 0

class SignalDataModel(BaseModel):
    direction: str
    vehicle_counts: VehicleCountsModel
    emergency_vehicle_present: bool = False
    signal_status: str
    signal_timer: int
    vehicles_crossed: int = 0
    avg_wait_time: float = 0.0
    green_time_allocated: Optional[int] = None
    queue_length: Optional[int] = None

class MetricsModel(BaseModel):
    total_vehicles_passed: int = 0
    avg_wait_time_all_sides: float = 0.0
    throughput: float = 0.0
    avg_speed: float = 0.0
    fuel_saved: float = 0.0
    co2_saved: float = 0.0
    emergency_overrides: int = 0
    cycle_time: Optional[int] = None

class SimulationDataModel(BaseModel):
    simulation_id: str
    timestamp: str
    intersection_id: Optional[str] = "INT_001"  # Default intersection
    signals: List[SignalDataModel]
    metrics: MetricsModel
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Invalid timestamp format')

class DataIngestionService:
    """
    Service for ingesting simulation JSON data into the database.
    Optimized for high-frequency inserts with batch processing.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ingestion")
        self.signal_cache = {}  # Cache for signal lookups
        self.emergency_coefficients = {
            'car': 0.8,      # Fuel savings coefficient per vehicle type
            'bus': 2.5,
            'truck': 3.2,
            'bike': 0.1,
            'rickshaw': 0.3
        }
        
    def _get_or_create_signal(self, db: Session, intersection_id: str, direction: str) -> Signal:
        """
        Get or create a signal for the given intersection and direction.
        Uses caching to minimize database lookups.
        """
        cache_key = f"{intersection_id}_{direction}"
        
        if cache_key in self.signal_cache:
            return self.signal_cache[cache_key]
        
        # Check if signal exists
        signal = db.query(Signal).filter(
            Signal.intersection_id == intersection_id,
            Signal.direction == direction
        ).first()
        
        if not signal:
            # Create new signal
            signal = Signal(
                intersection_id=intersection_id,
                direction=direction,
                lane_type='straight'
            )
            db.add(signal)
            db.flush()  # Get the ID without committing
        
        self.signal_cache[cache_key] = signal
        return signal
    
    def _ensure_simulation_exists(self, db: Session, simulation_id: str, mode: str = "ai") -> Simulation:
        """
        Ensure simulation record exists, create if not found.
        """
        simulation = db.query(Simulation).filter(
            Simulation.simulation_id == simulation_id
        ).first()
        
        if not simulation:
            simulation = Simulation(
                simulation_id=simulation_id,
                start_time=datetime.utcnow(),
                mode=mode,
                status='running'
            )
            db.add(simulation)
            db.flush()
        
        return simulation
    
    def _calculate_fuel_savings(self, vehicle_counts: Dict[str, int], avg_wait_time: float) -> float:
        """
        Calculate estimated fuel savings based on vehicle types and wait time reduction.
        """
        base_wait_time = 30.0  # Baseline wait time in seconds
        time_saved = max(0, base_wait_time - avg_wait_time)
        
        fuel_saved = 0.0
        for vehicle_type, count in vehicle_counts.items():
            coefficient = self.emergency_coefficients.get(vehicle_type, 0.5)
            fuel_saved += count * coefficient * (time_saved / 60.0) * 0.1  # L per minute saved
        
        return fuel_saved
    
    def _calculate_co2_savings(self, fuel_saved: float) -> float:
        """
        Calculate CO2 savings based on fuel savings.
        Approximate: 1 liter of fuel = 2.3 kg CO2
        """
        return fuel_saved * 2.3
    
    async def ingest_simulation_data(self, json_data: str) -> Dict[str, Any]:
        """
        Ingest simulation JSON data into the database.
        Returns ingestion statistics.
        """
        try:
            # Parse and validate JSON
            data = json.loads(json_data) if isinstance(json_data, str) else json_data
            simulation_data = SimulationDataModel(**data)
            
            timestamp = datetime.fromisoformat(simulation_data.timestamp.replace('Z', '+00:00'))
            
            with get_db_context() as db:
                # Ensure simulation exists
                simulation = self._ensure_simulation_exists(
                    db, simulation_data.simulation_id
                )
                
                # Ensure intersection exists
                intersection_id = simulation_data.intersection_id
                intersection = db.query(Intersection).filter(
                    Intersection.intersection_id == intersection_id
                ).first()
                
                if not intersection:
                    intersection = Intersection(
                        intersection_id=intersection_id,
                        location=f"Auto-created intersection {intersection_id}",
                        lanes=4
                    )
                    db.add(intersection)
                    db.flush()
                
                # Batch insert signal states and traffic data
                signal_states = []
                traffic_data_records = []
                
                for signal_data in simulation_data.signals:
                    signal = self._get_or_create_signal(
                        db, intersection_id, signal_data.direction
                    )
                    
                    # Create signal state record
                    signal_state = SignalState(
                        simulation_id=simulation_data.simulation_id,
                        signal_id=signal.signal_id,
                        timestamp=timestamp,
                        status=signal_data.signal_status,
                        timer_remaining=signal_data.signal_timer,
                        green_time_allocated=signal_data.green_time_allocated
                    )
                    signal_states.append(signal_state)
                    
                    # Create traffic data record
                    traffic_record = TrafficData(
                        simulation_id=simulation_data.simulation_id,
                        signal_id=signal.signal_id,
                        timestamp=timestamp,
                        vehicle_counts=signal_data.vehicle_counts.dict(),
                        emergency_vehicle_present=signal_data.emergency_vehicle_present,
                        vehicles_crossed=signal_data.vehicles_crossed,
                        avg_wait_time=signal_data.avg_wait_time,
                        queue_length=signal_data.queue_length or 0
                    )
                    traffic_data_records.append(traffic_record)
                
                # Batch insert signal states and traffic data
                db.add_all(signal_states)
                db.add_all(traffic_data_records)
                
                # Calculate enhanced fuel and CO2 savings
                total_vehicle_counts = {}
                for signal_data in simulation_data.signals:
                    for vehicle_type, count in signal_data.vehicle_counts.dict().items():
                        total_vehicle_counts[vehicle_type] = total_vehicle_counts.get(vehicle_type, 0) + count
                
                enhanced_fuel_saved = self._calculate_fuel_savings(
                    total_vehicle_counts, simulation_data.metrics.avg_wait_time_all_sides
                )
                enhanced_co2_saved = self._calculate_co2_savings(enhanced_fuel_saved)
                
                # Create performance metrics record
                performance_metric = PerformanceMetric(
                    simulation_id=simulation_data.simulation_id,
                    intersection_id=intersection_id,
                    timestamp=timestamp,
                    total_vehicles_passed=simulation_data.metrics.total_vehicles_passed,
                    avg_wait_time_all_sides=simulation_data.metrics.avg_wait_time_all_sides,
                    throughput=simulation_data.metrics.throughput,
                    avg_speed=simulation_data.metrics.avg_speed,
                    fuel_saved=max(simulation_data.metrics.fuel_saved, enhanced_fuel_saved),
                    co2_saved=max(simulation_data.metrics.co2_saved, enhanced_co2_saved),
                    emergency_overrides=simulation_data.metrics.emergency_overrides,
                    cycle_time=simulation_data.metrics.cycle_time
                )
                db.add(performance_metric)
                
                # Handle emergency events
                emergency_count = 0
                for signal_data in simulation_data.signals:
                    if signal_data.emergency_vehicle_present:
                        emergency_event = EmergencyEvent(
                            simulation_id=simulation_data.simulation_id,
                            signal_id=self._get_or_create_signal(
                                db, intersection_id, signal_data.direction
                            ).signal_id,
                            timestamp=timestamp,
                            event_type='emergency_override',
                            duration_seconds=signal_data.green_time_allocated,
                            delay_reduction=max(0, 30 - signal_data.avg_wait_time),
                            vehicles_affected=signal_data.vehicles_crossed
                        )
                        db.add(emergency_event)
                        emergency_count += 1
                
                db.commit()
                
                return {
                    "status": "success",
                    "simulation_id": simulation_data.simulation_id,
                    "timestamp": timestamp.isoformat(),
                    "records_inserted": {
                        "signal_states": len(signal_states),
                        "traffic_data": len(traffic_data_records),
                        "performance_metrics": 1,
                        "emergency_events": emergency_count
                    },
                    "processing_time_ms": 0  # Would be calculated in production
                }
        
        except Exception as e:
            self.logger.error(f"Error ingesting data: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "simulation_id": getattr(simulation_data, 'simulation_id', 'unknown')
            }
    
    async def batch_ingest(self, json_data_list: List[str]) -> Dict[str, Any]:
        """
        Batch ingest multiple simulation data points for better performance.
        """
        results = []
        successful = 0
        failed = 0
        
        for json_data in json_data_list:
            result = await self.ingest_simulation_data(json_data)
            results.append(result)
            
            if result["status"] == "success":
                successful += 1
            else:
                failed += 1
        
        return {
            "batch_status": "completed",
            "total_processed": len(json_data_list),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    def clear_cache(self):
        """Clear the signal cache. Useful when intersection configuration changes."""
        self.signal_cache = {}
        self.logger.info("Signal cache cleared")

# Global ingestion service instance
ingestion_service = DataIngestionService()