import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from database_config import get_db_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metrics_calculator")

class MetricsCalculator:
    """
    Service for calculating CO₂ and fuel savings metrics from traffic data.
    Runs as a scheduled task every 10 minutes.
    """
    
    def __init__(self):
        self.running = False
        self.task = None
        
        # Constants for calculations (these would be calibrated based on real-world data)
        self.CO2_PER_VEHICLE_IDLE_GRAM_PER_MINUTE = 150  # grams of CO2 per minute of idling
        self.FUEL_PER_VEHICLE_IDLE_ML_PER_MINUTE = 15    # ml of fuel per minute of idling
        
        # Vehicle type multipliers (relative to a standard car)
        self.vehicle_multipliers = {
            "car": 1.0,
            "bus": 3.5,
            "truck": 2.8,
            "bike": 0.3
        }
    
    async def start(self, interval_minutes: int = 10):
        """
        Start the metrics calculation scheduler.
        
        Args:
            interval_minutes: How often to run calculations (in minutes)
        """
        if self.running:
            logger.warning("Metrics calculator is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run_scheduler(interval_minutes))
        logger.info(f"Started metrics calculator with {interval_minutes} minute interval")
    
    async def stop(self):
        """
        Stop the metrics calculation scheduler.
        """
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped metrics calculator")
    
    async def _run_scheduler(self, interval_minutes: int):
        """
        Run the calculation task at regular intervals.
        
        Args:
            interval_minutes: How often to run calculations (in minutes)
        """
        try:
            while self.running:
                # Run the calculation
                await self.calculate_metrics()
                
                # Wait for the next interval
                await asyncio.sleep(interval_minutes * 60)
        except asyncio.CancelledError:
            logger.info("Metrics calculator scheduler cancelled")
        except Exception as e:
            logger.error(f"Error in metrics calculator scheduler: {e}")
            self.running = False
    
    async def calculate_metrics(self, time_window_minutes: int = 10):
        """
        Calculate CO₂ and fuel savings metrics from recent traffic data.
        
        Args:
            time_window_minutes: Time window for calculations (in minutes)
        """
        logger.info(f"Running metrics calculation for the last {time_window_minutes} minutes")
        
        try:
            # Calculate the time window
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)
            
            # Get active simulations
            active_simulations = await self._get_active_simulations()
            
            for sim in active_simulations:
                simulation_id = sim["simulation_id"]
                mode = sim["mode"]
                
                # Get intersections for this simulation
                intersections = await self._get_simulation_intersections(simulation_id)
                
                for intersection in intersections:
                    intersection_id = intersection["intersection_id"]
                    
                    # Get raw traffic data for this intersection and time window
                    traffic_data = await self._get_raw_traffic_data(
                        simulation_id, intersection_id, start_time, end_time
                    )
                    
                    if not traffic_data:
                        logger.warning(f"No traffic data found for simulation {simulation_id}, "
                                      f"intersection {intersection_id} in the specified time window")
                        continue
                    
                    # Calculate metrics
                    co2_saved, fuel_saved = self._calculate_savings(traffic_data, mode)
                    
                    # Store the calculated metrics
                    await self._store_calculated_metrics(
                        simulation_id, intersection_id, end_time, co2_saved, fuel_saved, time_window_minutes
                    )
                    
                    logger.info(f"Calculated metrics for simulation {simulation_id}, "
                              f"intersection {intersection_id}: CO₂ saved: {co2_saved}g, Fuel saved: {fuel_saved}ml")
        
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
    
    async def _get_active_simulations(self) -> List[Dict[str, Any]]:
        """
        Get a list of active simulations.
        
        Returns:
            List of active simulation records
        """
        with get_db_context() as db:
            result = db.execute("""
                SELECT simulation_id, mode 
                FROM simulations 
                WHERE status = 'running'
            """)
            
            return [dict(row) for row in result]
    
    async def _get_simulation_intersections(self, simulation_id: str) -> List[Dict[str, Any]]:
        """
        Get a list of intersections for a specific simulation.
        
        Args:
            simulation_id: The simulation ID
            
        Returns:
            List of intersection records
        """
        with get_db_context() as db:
            result = db.execute("""
                SELECT DISTINCT intersection_id 
                FROM raw_traffic_data 
                WHERE simulation_id = :simulation_id
            """, {"simulation_id": simulation_id})
            
            return [dict(row) for row in result]
    
    async def _get_raw_traffic_data(self, 
                                  simulation_id: str, 
                                  intersection_id: str, 
                                  start_time: datetime, 
                                  end_time: datetime) -> List[Dict[str, Any]]:
        """
        Get raw traffic data for a specific simulation, intersection, and time window.
        
        Args:
            simulation_id: The simulation ID
            intersection_id: The intersection ID
            start_time: Start of the time window
            end_time: End of the time window
            
        Returns:
            List of raw traffic data records
        """
        with get_db_context() as db:
            result = db.execute("""
                SELECT data 
                FROM raw_traffic_data 
                WHERE simulation_id = :simulation_id 
                AND intersection_id = :intersection_id 
                AND timestamp BETWEEN :start_time AND :end_time 
                ORDER BY timestamp
            """, {
                "simulation_id": simulation_id,
                "intersection_id": intersection_id,
                "start_time": start_time,
                "end_time": end_time
            })
            
            return [json.loads(row["data"]) for row in result]
    
    def _calculate_savings(self, traffic_data: List[Dict[str, Any]], mode: str) -> tuple:
        """
        Calculate CO₂ and fuel savings from traffic data.
        
        Args:
            traffic_data: List of traffic data records
            mode: Simulation mode ('baseline' or 'ai')
            
        Returns:
            Tuple of (co2_saved, fuel_saved)
        """
        total_co2_saved = 0.0
        total_fuel_saved = 0.0
        
        # If this is a baseline simulation, there are no savings
        if mode == "baseline":
            return (0.0, 0.0)
        
        # Process each data point
        for data in traffic_data:
            # Extract overall metrics
            overall_metrics = data.get("overall_metrics", {})
            avg_wait_time = overall_metrics.get("avg_wait_time_all_sides", 0)
            avg_speed = overall_metrics.get("avg_speed", 0)
            throughput = overall_metrics.get("throughput", 0)
            
            # Extract vehicle counts from all directions
            direction_metrics = data.get("direction_metrics", {})
            total_vehicles = {"car": 0, "bus": 0, "truck": 0, "bike": 0}
            
            for direction, metrics in direction_metrics.items():
                vehicle_counts = metrics.get("vehicle_counts", {})
                for vehicle_type, count in vehicle_counts.items():
                    if vehicle_type in total_vehicles:
                        total_vehicles[vehicle_type] += count
            
            # Calculate weighted vehicle count based on vehicle type
            weighted_vehicle_count = sum(
                count * self.vehicle_multipliers.get(vehicle_type, 1.0)
                for vehicle_type, count in total_vehicles.items()
            )
            
            # Estimate time saved based on average wait time reduction
            # Assuming a 30% reduction compared to baseline average wait time
            wait_time_reduction_minutes = (avg_wait_time * 0.3) / 60  # Convert to minutes
            
            # Calculate CO₂ and fuel savings for this data point
            co2_saved = weighted_vehicle_count * wait_time_reduction_minutes * self.CO2_PER_VEHICLE_IDLE_GRAM_PER_MINUTE
            fuel_saved = weighted_vehicle_count * wait_time_reduction_minutes * self.FUEL_PER_VEHICLE_IDLE_ML_PER_MINUTE
            
            # Add to totals
            total_co2_saved += co2_saved
            total_fuel_saved += fuel_saved
        
        return (total_co2_saved, total_fuel_saved)
    
    async def _store_calculated_metrics(self,
                                      simulation_id: str,
                                      intersection_id: str,
                                      timestamp: datetime,
                                      co2_saved: float,
                                      fuel_saved: float,
                                      calculation_period: int):
        """
        Store calculated metrics in the database.
        
        Args:
            simulation_id: The simulation ID
            intersection_id: The intersection ID
            timestamp: Timestamp for the metrics
            co2_saved: Amount of CO₂ saved (in grams)
            fuel_saved: Amount of fuel saved (in ml)
            calculation_period: Period over which metrics were calculated (in minutes)
        """
        with get_db_context() as db:
            # Store CO₂ saved metric
            db.execute("""
                INSERT INTO calculated_metrics 
                (simulation_id, intersection_id, timestamp, metric_type, value, calculation_period) 
                VALUES (:simulation_id, :intersection_id, :timestamp, 'co2_saved', :value, :period)
            """, {
                "simulation_id": simulation_id,
                "intersection_id": intersection_id,
                "timestamp": timestamp,
                "value": co2_saved,
                "period": f"{calculation_period}min"
            })
            
            # Store fuel saved metric
            db.execute("""
                INSERT INTO calculated_metrics 
                (simulation_id, intersection_id, timestamp, metric_type, value, calculation_period) 
                VALUES (:simulation_id, :intersection_id, :timestamp, 'fuel_saved', :value, :period)
            """, {
                "simulation_id": simulation_id,
                "intersection_id": intersection_id,
                "timestamp": timestamp,
                "value": fuel_saved,
                "period": f"{calculation_period}min"
            })

# Global instance of the metrics calculator
metrics_calculator = MetricsCalculator()