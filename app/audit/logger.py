import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class AuditLogger:
    """Structured audit logger for request tracking"""

    @staticmethod
    def log(
            request_id: str,
            operation_type: str,
            validation_outcome: Optional[Dict[str, Any]] = None,
            provider: Optional[str] = None,
            target_url: Optional[str] = None,
            upstream_status_code: Optional[int] = None,
            latency_ms: Optional[float] = None,
            final_outcome: Optional[str] = None,
            error: Optional[str] = None
    ):

        log_entry = {
            "requestId": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "operationType": operation_type,
        }

        if validation_outcome:
            log_entry["validationOutcome"] = validation_outcome

        if provider:
            log_entry["provider"] = provider

        if target_url:
            log_entry["targetUrl"] = target_url

        if upstream_status_code is not None:
            log_entry["upstreamStatusCode"] = upstream_status_code

        if latency_ms is not None:
            log_entry["latencyMs"] = round(latency_ms, 2)

        if final_outcome:
            log_entry["finalOutcome"] = final_outcome

        if error:
            log_entry["error"] = error

        print(json.dumps(log_entry))
