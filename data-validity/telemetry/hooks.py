"""
Non-blocking Runtime Telemetry Decorators & Context Management (§5.4)
Provides @perf_counter_hook for hooks 1, 2, 4, 6 and ContextVar request propagation.
"""

import os
import sys
import time
import functools
import logging
from contextvars import ContextVar
from typing import Any, Callable, Optional

current_dir = os.path.abspath(os.path.dirname(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .collector import TelemetryCollector
except (ImportError, ValueError):
    from collector import TelemetryCollector

logger = logging.getLogger(__name__)

# Request-scoped Telemetry ContextVar
_current_telemetry: ContextVar[Optional[TelemetryCollector]] = ContextVar("request_telemetry", default=None)


def get_current_telemetry() -> Optional[TelemetryCollector]:
    """Retrieve the TelemetryCollector for the active asynchronous request context."""
    return _current_telemetry.get()


def set_current_telemetry(collector: Optional[TelemetryCollector]) -> None:
    """Set the TelemetryCollector for the active asynchronous request context."""
    _current_telemetry.set(collector)


class TelemetryContext:
    """Context manager for scoping telemetry to a block or request lifecycle."""

    def __init__(self, collector: Optional[TelemetryCollector] = None):
        self.collector = collector or TelemetryCollector()
        self.token = None

    def __enter__(self) -> TelemetryCollector:
        self.token = _current_telemetry.set(self.collector)
        return self.collector

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token is not None:
            _current_telemetry.reset(self.token)


def perf_counter_hook(
    hook_type: str = "analytical_math",
    identifier_arg_name: Optional[str] = None,
) -> Callable:
    """
    Universal non-blocking perf_counter decorator for instrumentation hooks.
    hook_type options: "db_query", "analytical_math", "governance", "agent_swarm".
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - t0) * 1000.0
                try:
                    collector = get_current_telemetry()
                    if collector is not None:
                        if hook_type == "db_query":
                            collector.record_db_query(duration_ms)
                        elif hook_type == "analytical_math":
                            algo_name = kwargs.get(identifier_arg_name or "", fn.__name__)
                            collector.record_analytical_math(str(algo_name), duration_ms)
                        elif hook_type == "governance":
                            collector.record_governance(duration_ms, rules_evaluated=1, fired_rule_ids=[])
                        elif hook_type == "agent_swarm":
                            agent_name = kwargs.get(identifier_arg_name or "", fn.__name__)
                            collector.record_agent_execution(str(agent_name), duration_ms)
                except Exception as tel_err:
                    # Non-blocking: never let telemetry failure disrupt application logic
                    logger.debug(f"Telemetry hook failed silently: {tel_err}")

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return await fn(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - t0) * 1000.0
                try:
                    collector = get_current_telemetry()
                    if collector is not None:
                        if hook_type == "db_query":
                            collector.record_db_query(duration_ms)
                        elif hook_type == "analytical_math":
                            algo_name = kwargs.get(identifier_arg_name or "", fn.__name__)
                            collector.record_analytical_math(str(algo_name), duration_ms)
                        elif hook_type == "governance":
                            collector.record_governance(duration_ms, rules_evaluated=1, fired_rule_ids=[])
                        elif hook_type == "agent_swarm":
                            agent_name = kwargs.get(identifier_arg_name or "", fn.__name__)
                            collector.record_agent_execution(str(agent_name), duration_ms)
                except Exception as tel_err:
                    logger.debug(f"Telemetry hook async failed silently: {tel_err}")

        import inspect
        return async_wrapper if inspect.iscoroutinefunction(fn) else sync_wrapper

    return decorator
