import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.analytics import AnalyticsService

@pytest.fixture
def analytics_service():
    """Create analytics service fixture."""
    return AnalyticsService()

@pytest.mark.asyncio
async def test_get_simulation_summary_not_found(analytics_service):
    """Test simulation summary with non-existent simulation."""
    with patch('app.analytics.get_db_context') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value.__enter__.return_value = mock_session
        
        result = await analytics_service.get_simulation_summary("INVALID_ID")
        assert result["error"] == "Simulation not found"

@pytest.mark.asyncio 
async def test_get_average_wait_times_empty_data(analytics_service):
    """Test average wait times calculation with no data."""
    with patch('app.analytics.get_db_context') as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.join.return_value.group_by.return_value.all.return_value = []
        mock_db.return_value.__enter__.return_value = mock_session
        
        result = await analytics_service.get_average_wait_times()
        
        assert result["overall_avg_wait_time"] == 0
        assert result["best_performance"] is None
        assert result["worst_performance"] is None
        assert len(result["detailed_data"]) == 0

@pytest.mark.asyncio
async def test_get_environmental_impact_basic(analytics_service):
    """Test basic environmental impact calculation.""" 
    with patch('app.analytics.get_db_context') as mock_db:
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.simulation_id = "SIM_001"
        mock_result.mode = "ai"
        mock_result.total_fuel_saved = 10.5
        mock_result.total_co2_saved = 24.15
        mock_result.avg_fuel_saved = 2.1
        mock_result.avg_co2_saved = 4.83
        mock_result.data_points = 5
        
        mock_session.query.return_value.join.return_value.group_by.return_value.all.return_value = [mock_result]
        mock_db.return_value.__enter__.return_value = mock_session
        
        result = await analytics_service.get_environmental_impact()
        
        assert len(result["environmental_data"]) == 1
        assert result["environmental_data"][0]["simulation_id"] == "SIM_001"
        assert result["environmental_data"][0]["total_fuel_saved"] == 10.5
        assert result["total_fuel_saved"] == 10.5
        assert result["total_co2_saved"] == 24.15
