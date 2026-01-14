# models.py - SQLAlchemy ORM Models for Traffic Signal Simulation
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text, ForeignKey, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Simulation(Base):
    __tablename__ = "simulations"
    
    simulation_id = Column(String(50), primary_key=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    mode = Column(String(20), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='running')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    signal_states = relationship("SignalState", back_populates="simulation", cascade="all, delete-orphan")
    traffic_data = relationship("TrafficData", back_populates="simulation", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="simulation", cascade="all, delete-orphan")
    emergency_events = relationship("EmergencyEvent", back_populates="simulation", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("mode IN ('baseline', 'ai')", name='check_simulation_mode'),
        CheckConstraint("status IN ('running', 'completed', 'failed')", name='check_simulation_status'),
    )

class Intersection(Base):
    __tablename__ = "intersections"
    
    intersection_id = Column(String(50), primary_key=True)
    location = Column(String(200), nullable=False)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    lanes = Column(Integer, nullable=False, default=4)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    signals = relationship("Signal", back_populates="intersection", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="intersection")

class Signal(Base):
    __tablename__ = "signals"
    
    signal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intersection_id = Column(String(50), ForeignKey("intersections.intersection_id", ondelete="CASCADE"), nullable=False)
    direction = Column(String(20), nullable=False)
    lane_type = Column(String(20), nullable=False, default='straight')
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    intersection = relationship("Intersection", back_populates="signals")
    signal_states = relationship("SignalState", back_populates="signal", cascade="all, delete-orphan")
    traffic_data = relationship("TrafficData", back_populates="signal", cascade="all, delete-orphan")
    emergency_events = relationship("EmergencyEvent", back_populates="signal", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("direction IN ('north', 'south', 'east', 'west')", name='check_signal_direction'),
        CheckConstraint("lane_type IN ('straight', 'left', 'right', 'combined')", name='check_lane_type'),
    )

class SignalState(Base):
    __tablename__ = "signal_states"
    
    state_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(String(50), ForeignKey("simulations.simulation_id", ondelete="CASCADE"), nullable=False)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.signal_id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(10), nullable=False)
    timer_remaining = Column(Integer, nullable=False, default=0)
    green_time_allocated = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    simulation = relationship("Simulation", back_populates="signal_states")
    signal = relationship("Signal", back_populates="signal_states")
    
    __table_args__ = (
        CheckConstraint("status IN ('RED', 'GREEN', 'YELLOW')", name='check_signal_status'),
    )

class TrafficData(Base):
    __tablename__ = "traffic_data"
    
    traffic_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(String(50), ForeignKey("simulations.simulation_id", ondelete="CASCADE"), nullable=False)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.signal_id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    vehicle_counts = Column(JSONB, nullable=False)
    emergency_vehicle_present = Column(Boolean, default=False)
    vehicles_crossed = Column(Integer, default=0)
    avg_wait_time = Column(Numeric(8, 2), default=0.0)
    queue_length = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    simulation = relationship("Simulation", back_populates="traffic_data")
    signal = relationship("Signal", back_populates="traffic_data")

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(String(50), ForeignKey("simulations.simulation_id", ondelete="CASCADE"), nullable=False)
    intersection_id = Column(String(50), ForeignKey("intersections.intersection_id", ondelete="CASCADE"))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    total_vehicles_passed = Column(Integer, default=0)
    avg_wait_time_all_sides = Column(Numeric(8, 2), default=0.0)
    throughput = Column(Numeric(6, 4), default=0.0)
    avg_speed = Column(Numeric(6, 2), default=0.0)
    fuel_saved = Column(Numeric(10, 4), default=0.0)
    co2_saved = Column(Numeric(10, 4), default=0.0)
    emergency_overrides = Column(Integer, default=0)
    cycle_time = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    simulation = relationship("Simulation", back_populates="performance_metrics")
    intersection = relationship("Intersection", back_populates="performance_metrics")

class EmergencyEvent(Base):
    __tablename__ = "emergency_events"
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(String(50), ForeignKey("simulations.simulation_id", ondelete="CASCADE"), nullable=False)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.signal_id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String(50), nullable=False)
    duration_seconds = Column(Integer)
    delay_reduction = Column(Numeric(6, 2))
    vehicles_affected = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    simulation = relationship("Simulation", back_populates="emergency_events")
    signal = relationship("Signal", back_populates="emergency_events")
    
    __table_args__ = (
        CheckConstraint("event_type IN ('emergency_override', 'ambulance_detected', 'fire_truck_detected', 'police_detected')", name='check_event_type'),
    )