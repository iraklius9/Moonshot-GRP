import pytest
from unittest.mock import Mock, AsyncMock
from app.providers.base import SportsProvider
from app.providers.config import ProviderConfig


@pytest.fixture
def mock_provider():
    """Mock provider for testing"""
    provider = Mock(spec=SportsProvider)
    provider.list_leagues = AsyncMock(return_value=[{"id": "1", "name": "League 1"}])
    provider.get_league_matches = AsyncMock(return_value=[{"id": "m1", "league": "bl1"}])
    provider.get_team = AsyncMock(return_value={"id": "t1", "name": "Team 1"})
    provider.get_match = AsyncMock(return_value={"id": "m1", "status": "finished"})
    return provider


@pytest.fixture
def provider_config():
    """Provider config for testing"""
    return ProviderConfig()
