"""
SQLAlchemy models for traffic data
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class TrafficData(Base):
    __tablename__ = "traffic_data"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String(100), index=True)
    intersection_id = Column(String(100), index=True)
    timestamp = Column(DateTime, default=func.now())
    vehicle_count = Column(Integer)
    avg_wait_time = Column(Float)
    avg_speed = Column(Float)
    throughput = Column(Float)
    queue_length = Column(Float)
    signal_state = Column(String(20))
    created_at = Column(DateTime, default=func.now())

class EnvironmentalMetrics(Base):
    __tablename__ = "environmental_metrics"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String(100), index=True)
    intersection_id = Column(String(100), index=True)
    timestamp = Column(DateTime, default=func.now())
    fuel_consumption = Column(Float)  # liters
    co2_emissions = Column(Float)     # grams
    fuel_saved = Column(Float)        # liters saved vs baseline
    co2_saved = Column(Float)         # grams saved vs baseline
    created_at = Column(DateTime, default=func.now())

class EmergencyEvents(Base):
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String(100), index=True)
    intersection_id = Column(String(100), index=True)
    event_type = Column(String(50))   # "ambulance", "fire_truck", "police"
    timestamp = Column(DateTime, default=func.now())
    response_time = Column(Float)     # seconds
    priority_given = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class CalculatedMetrics(Base):
    __tablename__ = "calculated_metrics"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String(100), index=True)
    intersection_id = Column(String(100), index=True)
    metric_type = Column(String(50), index=True)  # "co2_saved", "fuel_saved", etc.
    value = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

class RawTrafficData(Base):
    __tablename__ = "raw_traffic_data"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String(100), index=True)
    intersection_id = Column(String(100), index=True)
    timestamp = Column(DateTime, default=func.now())
    data = Column(Text)  # JSON string of raw data
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())