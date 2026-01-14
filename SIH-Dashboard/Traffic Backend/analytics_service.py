# analytics.py - Analytics service for traffic simulation data
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text, desc
import logging
import numpy as np
from models import (
    Simulation, SignalState, TrafficData, PerformanceMetric, 
    EmergencyEvent, Signal, Intersection
)
from database import get_db_context

class AnalyticsService:
    """
    Service for performing analytics queries on traffic simulation data.
    Provides aggregated metrics and comparison capabilities.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("analytics")
    
    async def get_simulation_summary(self, simulation_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary for a specific simulation.
        """
        with get_db_context() as db:
            simulation = db.query(Simulation).filter(
                Simulation.simulation_id == simulation_id
            ).first()
            
            if not simulation:
                return {"error": "Simulation not found"}
            
            # Get basic stats
            total_metrics = db.query(PerformanceMetric).filter(
                PerformanceMetric.simulation_id == simulation_id
            ).count()
            
            # Get latest performance metrics
            latest_metric = db.query(PerformanceMetric).filter(
                PerformanceMetric.simulation_id == simulation_id
            ).order_by(desc(PerformanceMetric.timestamp)).first()
            
            # Get emergency events count
            emergency_count = db.query(EmergencyEvent).filter(
                EmergencyEvent.simulation_id == simulation_id
            ).count()
            
            return {
                "simulation_id": simulation_id,
                "mode": simulation.mode,
                "status": simulation.status,
                "start_time": simulation.start_time.isoformat(),
                "end_time": simulation.end_time.isoformat() if simulation.end_time else None,
                "total_data_points": total_metrics,
                "emergency_events": emergency_count,
                "latest_metrics": {
                    "avg_wait_time": float(latest_metric.avg_wait_time_all_sides) if latest_metric else 0,
                    "throughput": float(latest_metric.throughput) if latest_metric else 0,
                    "avg_speed": float(latest_metric.avg_speed) if latest_metric else 0,
                    "fuel_saved": float(latest_metric.fuel_saved) if latest_metric else 0,
                    "co2_saved": float(latest_metric.co2_saved) if latest_metric else 0
                }
            }
    
    async def get_average_wait_times(
        self, 
        simulation_id: Optional[str] = None,
        intersection_id: Optional[str] = None,
        time_window_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate average wait times with various grouping options.
        """
        with get_db_context() as db:
            query = db.query(
                TrafficData.simulation_id,
                Signal.intersection_id,
                Signal.direction,
                func.avg(TrafficData.avg_wait_time).label('avg_wait_time'),
                func.count(TrafficData.traffic_id).label('data_points'),
                func.min(TrafficData.timestamp).label('start_time'),
                func.max(TrafficData.timestamp).label('end_time')
            ).join(Signal, TrafficData.signal_id == Signal.signal_id)
            
            # Apply filters
            if simulation_id:
                query = query.filter(TrafficData.simulation_id == simulation_id)
            
            if intersection_id:
                query = query.filter(Signal.intersection_id == intersection_id)
            
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                query = query.filter(TrafficData.timestamp >= cutoff_time)
            
            # Group by simulation, intersection, and direction
            results = query.group_by(
                TrafficData.simulation_id,
                Signal.intersection_id,
                Signal.direction
            ).all()
            
            # Format results
            data = []
            for result in results:
                data.append({
                    "simulation_id": result.simulation_id,
                    "intersection_id": result.intersection_id,
                    "direction": result.direction,
                    "avg_wait_time": round(float(result.avg_wait_time), 2),
                    "data_points": result.data_points,
                    "time_period": {
                        "start": result.start_time.isoformat(),
                        "end": result.end_time.isoformat()
                    }
                })
            
            # Calculate overall statistics
            if data:
                overall_avg = sum(d['avg_wait_time'] for d in data) / len(data)
                best_performance = min(data, key=lambda x: x['avg_wait_time'])
                worst_performance = max(data, key=lambda x: x['avg_wait_time'])
            else:
                overall_avg = 0
                best_performance = worst_performance = None
            
            return {
                "overall_avg_wait_time": round(overall_avg, 2),
                "best_performance": best_performance,
                "worst_performance": worst_performance,
                "detailed_data": data,
                "total_intersections": len(set(d['intersection_id'] for d in data)),
                "total_simulations": len(set(d['simulation_id'] for d in data))
            }
    
    async def get_average_speeds(
        self,
        simulation_id: Optional[str] = None,
        intersection_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate average vehicle speeds across simulations.
        """
        with get_db_context() as db:
            query = db.query(
                PerformanceMetric.simulation_id,
                PerformanceMetric.intersection_id,
                func.avg(PerformanceMetric.avg_speed).label('avg_speed'),
                func.avg(PerformanceMetric.throughput).label('avg_throughput'),
                func.sum(PerformanceMetric.total_vehicles_passed).label('total_vehicles')
            )
            
            if simulation_id:
                query = query.filter(PerformanceMetric.simulation_id == simulation_id)
            
            if intersection_id:
                query = query.filter(PerformanceMetric.intersection_id == intersection_id)
            
            results = query.group_by(
                PerformanceMetric.simulation_id,
                PerformanceMetric.intersection_id
            ).all()
            
            data = []
            for result in results:
                data.append({
                    "simulation_id": result.simulation_id,
                    "intersection_id": result.intersection_id,
                    "avg_speed": round(float(result.avg_speed), 2),
                    "avg_throughput": round(float(result.avg_throughput), 4),
                    "total_vehicles": int(result.total_vehicles)
                })
            
            return {
                "speed_data": data,
                "overall_avg_speed": round(sum(d['avg_speed'] for d in data) / len(data), 2) if data else 0
            }
    
    async def get_environmental_impact(
        self,
        simulation_id: Optional[str] = None,
        comparison_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate fuel savings and CO2 reduction metrics.
        """
        with get_db_context() as db:
            query = db.query(
                PerformanceMetric.simulation_id,
                func.min(Simulation.mode).label("mode"),  # Keep this line as is
                func.sum(PerformanceMetric.fuel_saved).label('total_fuel_saved'),
                func.sum(PerformanceMetric.co2_saved).label('total_co2_saved'),
                func.avg(PerformanceMetric.fuel_saved).label('avg_fuel_saved'),
                func.avg(PerformanceMetric.co2_saved).label('avg_co2_saved'),
                func.count(PerformanceMetric.metric_id).label('data_points')
            ).join(Simulation, PerformanceMetric.simulation_id == Simulation.simulation_id)

            if simulation_id:
                query = query.filter(PerformanceMetric.simulation_id == simulation_id)

            # Group only by simulation_id (mode is already aggregated with func.min)
            results = query.group_by(
                PerformanceMetric.simulation_id
            ).all()

            data = []
            for result in results:
                data.append({
                    "simulation_id": result.simulation_id,
                    "mode": result.mode,
                    "total_fuel_saved": round(float(result.total_fuel_saved), 3),
                    "total_co2_saved": round(float(result.total_co2_saved), 3),
                    "avg_fuel_saved_per_cycle": round(float(result.avg_fuel_saved), 3),
                    "avg_co2_saved_per_cycle": round(float(result.avg_co2_saved), 3),
                    "data_points": result.data_points
                })

            return {
                "environmental_data": data,
                "total_fuel_saved": sum(d['total_fuel_saved'] for d in data),
                "total_co2_saved": sum(d['total_co2_saved'] for d in data)
            }


    async def get_baseline_vs_ai_comparison(
        self,
        metric: str = "wait_time",
        intersection_id: Optional[str] = None,
        time_window_hours: Optional[int] = 24
    ) -> Dict[str, Any]:
        """
        Compare baseline vs AI performance across multiple metrics.
        """
        with get_db_context() as db:
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                time_filter = PerformanceMetric.timestamp >= cutoff_time
            else:
                time_filter = True

            query = db.query(
                func.min(Simulation.mode).label("mode"),  # Aggregate mode
                func.avg(PerformanceMetric.avg_wait_time_all_sides).label('avg_wait_time'),
                func.avg(PerformanceMetric.avg_speed).label('avg_speed'),
                func.avg(PerformanceMetric.throughput).label('avg_throughput'),
                func.sum(PerformanceMetric.fuel_saved).label('total_fuel_saved'),
                func.sum(PerformanceMetric.co2_saved).label('total_co2_saved'),
                func.count(PerformanceMetric.metric_id).label('data_points'),
                func.avg(PerformanceMetric.total_vehicles_passed).label('avg_vehicles_passed')
            ).join(Simulation, PerformanceMetric.simulation_id == Simulation.simulation_id
            ).filter(time_filter)

            if intersection_id:
                query = query.filter(PerformanceMetric.intersection_id == intersection_id)

            # Group by simulation_id (mode aggregated)
            results = query.group_by(PerformanceMetric.simulation_id).all()

            comparison_data = {}
            for result in results:
                comparison_data[result.mode] = {
                    "avg_wait_time": round(float(result.avg_wait_time), 2),
                    "avg_speed": round(float(result.avg_speed), 2),
                    "avg_throughput": round(float(result.avg_throughput), 4),
                    "total_fuel_saved": round(float(result.total_fuel_saved), 3),
                    "total_co2_saved": round(float(result.total_co2_saved), 3),
                    "avg_vehicles_passed": round(float(result.avg_vehicles_passed), 1),
                    "data_points": result.data_points
                }

            # Calculate improvements
            improvements = {}
            if 'ai' in comparison_data and 'baseline' in comparison_data:
                ai_data = comparison_data['ai']
                baseline_data = comparison_data['baseline']

                wait_time_improvement = ((baseline_data['avg_wait_time'] - ai_data['avg_wait_time']) /
                                        baseline_data['avg_wait_time'] * 100) if baseline_data['avg_wait_time'] > 0 else 0
                speed_improvement = ((ai_data['avg_speed'] - baseline_data['avg_speed']) /
                                    baseline_data['avg_speed'] * 100) if baseline_data['avg_speed'] > 0 else 0
                throughput_improvement = ((ai_data['avg_throughput'] - baseline_data['avg_throughput']) /
                                        baseline_data['avg_throughput'] * 100) if baseline_data['avg_throughput'] > 0 else 0

                improvements = {
                    "wait_time_reduction_pct": round(wait_time_improvement, 2),
                    "speed_improvement_pct": round(speed_improvement, 2),
                    "throughput_improvement_pct": round(throughput_improvement, 2),
                    "additional_fuel_saved": round(ai_data['total_fuel_saved'] - baseline_data['total_fuel_saved'], 3),
                    "additional_co2_saved": round(ai_data['total_co2_saved'] - baseline_data['total_co2_saved'], 3)
                }

            return {
                "comparison_data": comparison_data,
                "improvements": improvements,
                "time_window_hours": time_window_hours,
                "intersection_id": intersection_id
            }

    
    async def get_emergency_handling_report(
        self,
        simulation_id: Optional[str] = None,
        time_window_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate report on emergency vehicle handling performance.
        """
        with get_db_context() as db:
            query = db.query(
                EmergencyEvent.simulation_id,
                EmergencyEvent.event_type,
                func.count(EmergencyEvent.event_id).label('event_count'),
                func.avg(EmergencyEvent.delay_reduction).label('avg_delay_reduction'),
                func.sum(EmergencyEvent.vehicles_affected).label('total_vehicles_affected'),
                func.avg(EmergencyEvent.duration_seconds).label('avg_duration')
            )
            
            # Apply filters
            if simulation_id:
                query = query.filter(EmergencyEvent.simulation_id == simulation_id)
            
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                query = query.filter(EmergencyEvent.timestamp >= cutoff_time)
            
            # Group by simulation and event type
            results = query.group_by(
                EmergencyEvent.simulation_id,
                EmergencyEvent.event_type
            ).all()
            
            # Process emergency data
            emergency_data = []
            for result in results:
                emergency_data.append({
                    "simulation_id": result.simulation_id,
                    "event_type": result.event_type,
                    "event_count": result.event_count,
                    "avg_delay_reduction": round(float(result.avg_delay_reduction or 0), 2),
                    "total_vehicles_affected": int(result.total_vehicles_affected or 0),
                    "avg_duration_seconds": round(float(result.avg_duration or 0), 1)
                })
            
            # Calculate summary statistics
            total_events = sum(d['event_count'] for d in emergency_data)
            total_delay_reduction = sum(d['avg_delay_reduction'] * d['event_count'] for d in emergency_data)
            avg_delay_reduction = total_delay_reduction / total_events if total_events > 0 else 0
            
            return {
                "emergency_events": emergency_data,
                "summary": {
                    "total_emergency_events": total_events,
                    "avg_delay_reduction_seconds": round(avg_delay_reduction, 2),
                    "total_vehicles_helped": sum(d['total_vehicles_affected'] for d in emergency_data),
                    "most_common_event_type": max(emergency_data, key=lambda x: x['event_count'])['event_type'] if emergency_data else None
                }
            }
    
    async def get_time_series_data(
        self,
        simulation_id: str,
        metric: str = "wait_time",
        interval_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Get time-series data for charts and visualizations.
        """
        with get_db_context() as db:
            # Create time buckets for aggregation
            time_bucket = func.date_trunc('minute', 
                func.floor(func.extract('epoch', PerformanceMetric.timestamp) / (interval_minutes * 60)) * (interval_minutes * 60)
            )
            
            query = db.query(
                time_bucket.label('time_bucket'),
                func.avg(PerformanceMetric.avg_wait_time_all_sides).label('avg_wait_time'),
                func.avg(PerformanceMetric.avg_speed).label('avg_speed'),
                func.avg(PerformanceMetric.throughput).label('throughput'),
                func.sum(PerformanceMetric.total_vehicles_passed).label('vehicles_passed')
            ).filter(
                PerformanceMetric.simulation_id == simulation_id
            ).group_by(time_bucket).order_by(time_bucket)
            
            results = query.all()
            
            # Format for chart consumption
            chart_data = []
            for result in results:
                chart_data.append({
                    "timestamp": result.time_bucket.isoformat(),
                    "avg_wait_time": round(float(result.avg_wait_time), 2),
                    "avg_speed": round(float(result.avg_speed), 2),
                    "throughput": round(float(result.throughput), 4),
                    "vehicles_passed": int(result.vehicles_passed)
                })
            
            return {
                "simulation_id": simulation_id,
                "interval_minutes": interval_minutes,
                "data_points": len(chart_data),
                "time_series": chart_data
            }

# Global analytics service instance
analytics_service = AnalyticsService()