import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request
from starlette.responses import Response
from app.middleware.logging import RequestResponseLoggingMiddleware, SENSITIVE_HEADERS


class TestRequestResponseLoggingMiddleware:
    """Test middleware functionality"""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance"""
        app = Mock()
        return RequestResponseLoggingMiddleware(app)

    @pytest.mark.asyncio
    async def test_sanitize_headers(self, middleware):
        """Test header sanitization"""
        request = Mock(spec=Request)
        request.headers = {
            "authorization": "Bearer secret",
            "x-api-key": "key123",
            "content-type": "application/json",
            "user-agent": "test"
        }
        request.method = "GET"
        request.url.path = "/test"

        sanitized = {}
        for key, value in request.headers.items():
            if key.lower() not in SENSITIVE_HEADERS:
                sanitized[key] = value
            else:
                sanitized[key] = "[REDACTED]"

        assert sanitized["authorization"] == "[REDACTED]"
        assert sanitized["x-api-key"] == "[REDACTED]"
        assert sanitized["content-type"] == "application/json"
        assert sanitized["user-agent"] == "test"

    @pytest.mark.asyncio
    async def test_log_request_with_body(self, middleware):
        """Test request logging with body"""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/proxy/execute"
        headers_mock = Mock()
        headers_mock.items.return_value = [("content-type", "application/json")]
        headers_mock.get.return_value = None
        request.headers = headers_mock

        body = b'{"operationType": "ListLeagues", "payload": {}}'
        request.body = AsyncMock(return_value=body)

        with patch('builtins.print') as mock_print:
            await middleware._log_request(request, "test-id", len(body), body.decode("utf-8")[:500])

            assert mock_print.called
            call_args = mock_print.call_args[0][0]
            log_data = json.loads(call_args)
            assert log_data["requestId"] == "test-id"
            assert log_data["method"] == "POST"
            assert log_data["bodySize"] == len(body)

    @pytest.mark.asyncio
    async def test_log_response(self, middleware):
        """Test response logging"""
        response = Response(content='{"success": true}', status_code=200)

        with patch('builtins.print') as mock_print:
            await middleware._log_response(response, "test-id", 123.45)

            assert mock_print.called
            call_args = mock_print.call_args[0][0]
            log_data = json.loads(call_args)
            assert log_data["requestId"] == "test-id"
            assert log_data["statusCode"] == 200
            assert log_data["latencyMs"] == 123.45
