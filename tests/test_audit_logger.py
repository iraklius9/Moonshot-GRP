import json
from unittest.mock import patch
from app.audit.logger import AuditLogger


class TestAuditLogger:
    """Test audit logger functionality"""

    def test_log_success(self):
        """Test logging successful operation"""
        with patch('builtins.print') as mock_print:
            AuditLogger.log(
                request_id="test-id",
                operation_type="ListLeagues",
                validation_outcome={"pass": True},
                provider="OpenLiga",
                target_url="https://api.example.com/leagues",
                upstream_status_code=200,
                latency_ms=123.45,
                final_outcome="success"
            )

            assert mock_print.called
            call_args = mock_print.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["requestId"] == "test-id"
            assert log_data["operationType"] == "ListLeagues"
            assert log_data["validationOutcome"]["pass"] is True
            assert log_data["provider"] == "OpenLiga"
            assert log_data["upstreamStatusCode"] == 200
            assert log_data["latencyMs"] == 123.45
            assert log_data["finalOutcome"] == "success"

    def test_log_validation_failure(self):
        """Test logging validation failure"""
        with patch('builtins.print') as mock_print:
            AuditLogger.log(
                request_id="test-id",
                operation_type="GetLeagueMatches",
                validation_outcome={"pass": False, "reasons": ["Missing leagueId"]},
                final_outcome="error",
                error="Validation failed"
            )

            assert mock_print.called
            call_args = mock_print.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["validationOutcome"]["pass"] is False
            assert log_data["finalOutcome"] == "error"
            assert log_data["error"] == "Validation failed"

    def test_log_minimal_fields(self):
        """Test logging with minimal fields"""
        with patch('builtins.print') as mock_print:
            AuditLogger.log(
                request_id="test-id",
                operation_type="ListLeagues"
            )

            assert mock_print.called
            call_args = mock_print.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["requestId"] == "test-id"
            assert log_data["operationType"] == "ListLeagues"
            assert "timestamp" in log_data
