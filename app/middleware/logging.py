import json
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

SENSITIVE_HEADERS = {
    "authorization",
    "api-key",
    "x-api-key",
    "cookie",
    "set-cookie",
    "x-auth-token",
    "x-access-token",
}


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request and response metadata"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        body = b""
        body_preview = None
        body_size = 0

        if request.method == "POST":
            body = await request.body()
            body_size = len(body)
            if body:
                try:
                    body_str = body.decode("utf-8")
                    body_preview = body_str[:500] if len(body_str) > 500 else body_str
                except Exception:
                    body_preview = "[BINARY]"

            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

        start_time = time.time()
        await self._log_request(request, request_id, body_size, body_preview)

        response = await call_next(request)

        latency_ms = (time.time() - start_time) * 1000

        await self._log_response(response, request_id, latency_ms)

        response.headers["X-Request-ID"] = request_id

        return response

    @staticmethod
    async def _log_request(request: Request, request_id: str, body_size: int, body_preview: str = None):
        """Log inbound request metadata"""
        sanitized_headers = {}
        for key, value in request.headers.items():
            if key.lower() not in SENSITIVE_HEADERS:
                sanitized_headers[key] = value
            else:
                sanitized_headers[key] = "[REDACTED]"

        log_entry = {
            "type": "request",
            "requestId": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "headers": sanitized_headers,
            "bodySize": body_size,
        }

        if body_preview:
            log_entry["bodyPreview"] = body_preview

        print(json.dumps(log_entry))

    @staticmethod
    async def _log_response(response: Response, request_id: str, latency_ms: float):
        """Log outbound response metadata"""
        body_size = 0
        if hasattr(response, "body"):
            body_size = len(response.body) if response.body else 0

        log_entry = {
            "type": "response",
            "requestId": request_id,
            "statusCode": response.status_code,
            "bodySize": body_size,
            "latencyMs": round(latency_ms, 2),
        }

        print(json.dumps(log_entry))
