import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from .models.request import ProxyRequest
from .models.response import ProxyResponse
from .providers.openliga import OpenLigaProvider
from .decision_mapper import DecisionMapper
from .providers.config import ProviderConfig
from .providers import get_provider
from .middleware.logging import RequestResponseLoggingMiddleware
from .audit.logger import AuditLogger
import httpx

provider: OpenLigaProvider = None
decision_mapper: DecisionMapper = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global provider, decision_mapper

    config = ProviderConfig()
    provider = get_provider(config)
    decision_mapper = DecisionMapper(provider)
    yield

    if provider:
        await provider.close()


app = FastAPI(
    title="Reverse Proxy Service",
    description="Generic reverse proxy to external APIs",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(RequestResponseLoggingMiddleware)


@app.post("/proxy/execute", response_model=ProxyResponse)
async def execute_proxy(request: Request, proxy_request: ProxyRequest):
    """
    Execute a proxy operation based on operationType

    Request body:
    - operationType: Type of operation (ListLeagues, GetLeagueMatches, GetTeam, GetMatch)
    - payload: Operation-specific payload fields
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()
    operation_type = proxy_request.operationType
    payload = proxy_request.payload or {}

    try:
        try:
            operation = decision_mapper.get_operation(operation_type)
        except ValueError as e:
            error_msg = str(e)
            AuditLogger.log(
                request_id=request_id,
                operation_type=operation_type,
                validation_outcome={"pass": False, "reasons": [error_msg]},
                final_outcome="error",
                error=error_msg
            )
            raise HTTPException(
                status_code=400,
                detail={"error": error_msg, "requestId": request_id}
            )

        is_valid, validation_details = operation["validate"](payload)
        if not is_valid:
            validation_outcome = {
                "pass": False,
                "reasons": [validation_details.get("reason", "Validation failed")]
            }
            AuditLogger.log(
                request_id=request_id,
                operation_type=operation_type,
                validation_outcome=validation_outcome,
                final_outcome="error",
                error="Validation failed"
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation failed",
                    "details": validation_details,
                    "requestId": request_id
                }
            )

        AuditLogger.log(
            request_id=request_id,
            operation_type=operation_type,
            validation_outcome={"pass": True},
            provider="OpenLiga"
        )

        try:
            upstream_start = time.time()
            result = await operation["execute"](payload)
            upstream_latency = (time.time() - upstream_start) * 1000

            normalized_data = operation["normalize"](result)

            AuditLogger.log(
                request_id=request_id,
                operation_type=operation_type,
                provider="OpenLiga",
                target_url=f"{ProviderConfig().OPENLIGA_BASE_URL}/...",
                upstream_status_code=200,
                latency_ms=upstream_latency,
                final_outcome="success"
            )

            return ProxyResponse(
                success=True,
                data=normalized_data,
                requestId=request_id
            )

        except httpx.HTTPStatusError as e:
            latency_ms = (time.time() - start_time) * 1000
            AuditLogger.log(
                request_id=request_id,
                operation_type=operation_type,
                provider="OpenLiga",
                target_url=f"{ProviderConfig().OPENLIGA_BASE_URL}/...",
                upstream_status_code=e.response.status_code,
                latency_ms=latency_ms,
                final_outcome="error",
                error="Upstream API failed"
            )
            raise HTTPException(
                status_code=502,
                detail={"error": "Upstream API failed", "requestId": request_id}
            )
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            latency_ms = (time.time() - start_time) * 1000
            AuditLogger.log(
                request_id=request_id,
                operation_type=operation_type,
                provider="OpenLiga",
                target_url=f"{ProviderConfig().OPENLIGA_BASE_URL}/...",
                latency_ms=latency_ms,
                final_outcome="error",
                error=f"Network error: {str(e)}"
            )
            raise HTTPException(
                status_code=502,
                detail={"error": "Upstream API failed", "requestId": request_id}
            )
        except ValueError as e:
            error_msg = str(e)
            latency_ms = (time.time() - start_time) * 1000

            if "not found" in error_msg.lower():
                status_code = 404
            else:
                status_code = 400

            AuditLogger.log(
                request_id=request_id,
                operation_type=operation_type,
                provider="OpenLiga",
                latency_ms=latency_ms,
                final_outcome="error",
                error=error_msg
            )
            raise HTTPException(
                status_code=status_code,
                detail={"error": error_msg, "requestId": request_id}
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            AuditLogger.log(
                request_id=request_id,
                operation_type=operation_type,
                provider="OpenLiga",
                latency_ms=latency_ms,
                final_outcome="error",
                error=str(e)
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal server error", "requestId": request_id}
            )

    except HTTPException:
        raise
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        AuditLogger.log(
            request_id=request_id,
            operation_type=operation_type,
            latency_ms=latency_ms,
            final_outcome="error",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "requestId": request_id}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
