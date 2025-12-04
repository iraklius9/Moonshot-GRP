import pytest
from pydantic import ValidationError
from app.models.request import ProxyRequest
from app.models.response import ProxyResponse, ErrorResponse


class TestProxyRequest:
    """Test request models"""

    def test_valid_request(self):
        """Test valid proxy request"""
        request = ProxyRequest(
            operationType="ListLeagues",
            payload={}
        )
        assert request.operationType == "ListLeagues"
        assert request.payload == {}

    def test_request_with_payload(self):
        """Test request with payload"""
        request = ProxyRequest(
            operationType="GetLeagueMatches",
            payload={"leagueId": "bl1"}
        )
        assert request.operationType == "GetLeagueMatches"
        assert request.payload["leagueId"] == "bl1"

    def test_missing_operation_type(self):
        """Test missing operationType raises error"""
        with pytest.raises(ValidationError):
            ProxyRequest(payload={})


class TestProxyResponse:
    """Test response models"""

    def test_success_response(self):
        """Test successful response"""
        response = ProxyResponse(
            success=True,
            data={"leagues": []},
            requestId="test-id"
        )
        assert response.success is True
        assert response.data == {"leagues": []}
        assert response.requestId == "test-id"

    def test_error_response(self):
        """Test error response"""
        error = ErrorResponse(
            error="Test error",
            details={"field": "value"},
            requestId="test-id"
        )
        assert error.error == "Test error"
        assert error.details == {"field": "value"}
        assert error.requestId == "test-id"
