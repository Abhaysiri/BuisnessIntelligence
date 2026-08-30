import time
from uuid import uuid4
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request-scoped telemetry propagation (§5.4 Hook 1)
request_telemetry_ctx: ContextVar[Dict[str, Any]] = ContextVar("request_telemetry", default={})


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Hook 1: FastAPI Request Lifecycle Middleware (§5.4, §8.1).
    Measures total_latency_ms, captures request metadata, tracks execution context,
    and injects X-Trace-ID, X-Latency-MS, and X-Total-Cost-USD response headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Extract or generate correlation trace ID
        incoming_trace_id = request.headers.get("X-Trace-ID") or request.headers.get("x-trace-id")
        trace_id = incoming_trace_id or f"tr-{uuid4().hex[:8]}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"

        tenant_id = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id") or "anonymous"

        # Initialize request-scoped telemetry context
        telemetry_data: Dict[str, Any] = {
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "endpoint": request.url.path,
            "method": request.method,
            "start_time": start_time,
            "total_latency_ms": 0.0,
            "cost_usd": 0.0,
            "db_latency_ms": 0.0,
            "agent_latency_ms": 0.0,
            "analytics_latency_ms": 0.0,
            "orchestrator_llm_latency_ms": 0.0,
            "governance_latency_ms": 0.0,
            "persona_llm_latency_ms": 0.0,
        }
        token = request_telemetry_ctx.set(telemetry_data)

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            # Calculate latency even on unhandled exceptions
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            telemetry_data["total_latency_ms"] = duration_ms
            request_telemetry_ctx.reset(token)
            raise exc

        # Calculate final total latency
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        telemetry_data["total_latency_ms"] = duration_ms
        telemetry_data["status_code"] = response.status_code

        # Retrieve estimated cost if updated during request lifecycle
        cost_usd = telemetry_data.get("cost_usd", 0.0)

        # Inject telemetry response headers (§5.4 Hook 1)
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Latency-MS"] = f"{duration_ms:.2f}"
        response.headers["X-Total-Cost-USD"] = f"{cost_usd:.5f}"

        request_telemetry_ctx.reset(token)
        return response


def get_current_telemetry_context() -> Dict[str, Any]:
    """Retrieve the current request's telemetry context dict."""
    return request_telemetry_ctx.get()


def record_subsystem_latency(subsystem_key: str, latency_ms: float) -> None:
    """Record execution latency for a specific subsystem in the active request context."""
    ctx = request_telemetry_ctx.get()
    if ctx:
        ctx[subsystem_key] = ctx.get(subsystem_key, 0.0) + latency_ms


def record_request_cost(cost_usd: float) -> None:
    """Record LLM token cost in the active request context."""
    ctx = request_telemetry_ctx.get()
    if ctx:
        ctx["cost_usd"] = ctx.get("cost_usd", 0.0) + cost_usd
