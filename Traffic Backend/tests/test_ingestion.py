import pytest
import json
from app.ingestion import SimulationDataModel, VehicleCountsModel, SignalDataModel, MetricsModel

def test_simulation_data_model():
    """Test SimulationDataModel validation."""
    sample_data = {
        "simulation_id": "SIM_001",
        "timestamp": "2023-12-01T10:00:00Z",
        "intersection_id": "INT_001",
        "signals": [
            {
                "direction": "north",
                "vehicle_counts": {
                    "car": 10,
                    "bus": 1,
                    "truck": 0,
                    "bike": 2,
                    "rickshaw": 0
                },
                "emergency_vehicle_present": False,
                "signal_status": "GREEN",
                "signal_timer": 30,
                "vehicles_crossed": 5,
                "avg_wait_time": 15.2,
                "green_time_allocated": 45,
                "queue_length": 3
            }
        ],
        "metrics": {
            "total_vehicles_passed": 20,
            "avg_wait_time_all_sides": 18.5,
            "throughput": 0.75,
            "avg_speed": 35.2,
            "fuel_saved": 2.3,
            "co2_saved": 5.29,
            "emergency_overrides": 0,
            "cycle_time": 120
        }
    }
    
    # Should not raise validation error
    model = SimulationDataModel(**sample_data)
    assert model.simulation_id == "SIM_001"
    assert model.intersection_id == "INT_001"
    assert len(model.signals) == 1
    assert model.metrics.total_vehicles_passed == 20

def test_vehicle_counts_model():
    """Test VehicleCountsModel validation."""
    data = {
        "car": 15,
        "bus": 2,
        "truck": 1,
        "bike": 5,
        "rickshaw": 3
    }
    
    model = VehicleCountsModel(**data)
    assert model.car == 15
    assert model.bus == 2
    assert model.bike == 5

def test_invalid_timestamp():
    """Test validation with invalid timestamp."""
    invalid_data = {
        "simulation_id": "SIM_001",
        "timestamp": "invalid-timestamp",
        "signals": [],
        "metrics": {}
    }
    
    with pytest.raises(ValueError, match="Invalid timestamp format"):
        SimulationDataModel(**invalid_data)
