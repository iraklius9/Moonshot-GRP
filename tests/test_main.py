import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestMainEndpoint:
    """Test main endpoint functionality"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @patch('app.main.decision_mapper')
    @patch('app.main.provider')
    def test_list_leagues_success(self, mock_provider, mock_mapper, client):
        """Test successful ListLeagues operation"""
        # Setup mocks
        operation = {
            "validate": lambda p: (True, None),
            "execute": AsyncMock(return_value=[{"id": "1", "name": "League 1"}]),
            "normalize": lambda d: {"leagues": d, "count": len(d)}
        }
        mock_mapper.get_operation.return_value = operation

        response = client.post(
            "/proxy/execute",
            json={
                "operationType": "ListLeagues",
                "payload": {}
            },
            headers={"X-Request-ID": "test-id"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "leagues" in data["data"]
        assert data["requestId"] == "test-id"

    @patch('app.main.decision_mapper')
    def test_unknown_operation_type(self, mock_mapper, client):
        """Test unknown operationType returns 400"""
        mock_mapper.get_operation.side_effect = ValueError("Unknown operationType: InvalidOp")

        response = client.post(
            "/proxy/execute",
            json={
                "operationType": "InvalidOp",
                "payload": {}
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert "InvalidOp" in data["detail"]["error"]

    @patch('app.main.decision_mapper')
    def test_validation_failure(self, mock_mapper, client):
        """Test validation failure returns 400"""
        operation = {
            "validate": lambda p: (False, {"missing_field": "leagueId", "reason": "leagueId is required"}),
            "execute": AsyncMock(),
            "normalize": lambda d: d
        }
        mock_mapper.get_operation.return_value = operation

        response = client.post(
            "/proxy/execute",
            json={
                "operationType": "GetLeagueMatches",
                "payload": {}
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "Validation failed"

    @patch('app.main.decision_mapper')
    @patch('app.main.provider')
    def test_upstream_failure(self, mock_provider, mock_mapper, client):
        """Test upstream failure returns 502"""
        import httpx

        operation = {
            "validate": lambda p: (True, None),
            "execute": AsyncMock(side_effect=httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )),
            "normalize": lambda d: d
        }
        mock_mapper.get_operation.return_value = operation

        response = client.post(
            "/proxy/execute",
            json={
                "operationType": "ListLeagues",
                "payload": {}
            }
        )

        assert response.status_code == 502
        data = response.json()
        assert "error" in data["detail"]
        assert "Upstream API failed" in data["detail"]["error"]
