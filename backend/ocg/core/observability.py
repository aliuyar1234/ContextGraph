from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import re
from secrets import token_hex
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=("route", "method", "status"),
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    labelnames=("route",),
)
AUTH_FAILURES = Counter("auth_failures_total", "Authentication failures")
PERMISSION_UNKNOWN = Counter(
    "permission_unknown_records_total",
    "Count of records excluded due to unknown permissions",
)
PATTERNS_PUBLISHED = Counter("patterns_published_total", "Published context patterns")
PATTERNS_DROPPED_K_ANON = Counter("patterns_dropped_k_anon_total", "Dropped patterns")
ABSTRACT_TRACES_CREATED = Counter("abstract_traces_created_total", "Abstract traces created")
CONNECTOR_FETCH_DURATION = Histogram(
    "connector_fetch_duration_seconds", "Connector fetch duration", labelnames=("tool",)
)
CONNECTOR_ERRORS = Counter(
    "connector_errors_total", "Connector errors", labelnames=("tool", "reason")
)
INGEST_EVENTS_TOTAL = Counter("ingest_events_total", "Ingested events", labelnames=("tool",))
INGEST_BACKLOG_DEPTH = Gauge("ingest_backlog_depth", "Backlog depth", labelnames=("queue",))
RATE_LIMITED_TOTAL = Counter("rate_limited_total", "Rate limited responses", labelnames=("tool",))
AGGREGATION_JOB_DURATION = Histogram("aggregation_job_duration_seconds", "Aggregation job runtime")
WORKER_JOBS_TOTAL = Counter("worker_jobs_total", "Worker jobs", labelnames=("job", "status"))
WORKER_JOB_DURATION = Histogram(
    "worker_job_duration_seconds",
    "Worker job runtime",
    labelnames=("job",),
)
TRACE_SPANS_TOTAL = Counter("trace_spans_total", "Trace spans", labelnames=("span", "status"))
TRACE_SPAN_DURATION = Histogram(
    "trace_span_duration_seconds",
    "Trace span duration",
    labelnames=("span",),
)


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None


TRACEPARENT_PATTERN = re.compile(
    r"^(?P<version>[0-9a-f]{2})-(?P<trace_id>[0-9a-f]{32})-(?P<span_id>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)
_TRACE_CONTEXT: ContextVar[TraceContext | None] = ContextVar("trace_context", default=None)


def _parse_traceparent(traceparent: str | None) -> tuple[str, str] | None:
    if not traceparent:
        return None
    candidate = traceparent.strip().lower()
    match = TRACEPARENT_PATTERN.match(candidate)
    if not match:
        return None
    return (match.group("trace_id"), match.group("span_id"))


def _new_trace_context(traceparent: str | None) -> TraceContext:
    parsed = _parse_traceparent(traceparent)
    if not parsed:
        return TraceContext(trace_id=token_hex(16), span_id=token_hex(8))
    trace_id, parent_span_id = parsed
    return TraceContext(trace_id=trace_id, span_id=token_hex(8), parent_span_id=parent_span_id)


def _route_label(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    return template or request.url.path


def current_trace_context() -> TraceContext | None:
    return _TRACE_CONTEXT.get()


@contextmanager
def traced_span(span_name: str):
    parent = current_trace_context()
    if parent is None:
        context = TraceContext(trace_id=token_hex(16), span_id=token_hex(8))
    else:
        context = TraceContext(
            trace_id=parent.trace_id, span_id=token_hex(8), parent_span_id=parent.span_id
        )
    token = _TRACE_CONTEXT.set(context)
    status = "ok"
    start = perf_counter()
    try:
        yield context
    except Exception:
        status = "error"
        raise
    finally:
        elapsed = perf_counter() - start
        TRACE_SPANS_TOTAL.labels(span=span_name, status=status).inc()
        TRACE_SPAN_DURATION.labels(span=span_name).observe(elapsed)
        _TRACE_CONTEXT.reset(token)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-Id", f"req_{uuid4().hex[:12]}")
        context = _new_trace_context(request.headers.get("traceparent"))
        token = _TRACE_CONTEXT.set(context)
        request.state.request_id = request_id
        request.state.trace_id = context.trace_id
        request.state.span_id = context.span_id
        method = request.method
        start = perf_counter()
        try:
            with traced_span("http.request"):
                response = await call_next(request)
        finally:
            _TRACE_CONTEXT.reset(token)

        route = _route_label(request)
        elapsed = perf_counter() - start
        HTTP_REQUESTS.labels(route=route, method=method, status=str(response.status_code)).inc()
        HTTP_DURATION.labels(route=route).observe(elapsed)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Trace-Id"] = context.trace_id
        response.headers["traceparent"] = f"00-{context.trace_id}-{context.span_id}-01"
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
