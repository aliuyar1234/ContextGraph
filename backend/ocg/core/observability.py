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


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-Id", f"req_{uuid4().hex[:12]}")
        request.state.request_id = request_id
        route = request.url.path
        method = request.method
        start = perf_counter()
        response = await call_next(request)
        elapsed = perf_counter() - start
        HTTP_REQUESTS.labels(route=route, method=method, status=str(response.status_code)).inc()
        HTTP_DURATION.labels(route=route).observe(elapsed)
        response.headers["X-Request-Id"] = request_id
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
