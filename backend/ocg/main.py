from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from ocg.api import routes_admin, routes_analytics, routes_health, routes_personal, routes_suggest
from ocg.core.observability import PrometheusMiddleware
from ocg.core.security import validate_startup_security
from ocg.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    validate_startup_security(settings)
    app = FastAPI(title="Open Context Graph API", version="1.0.0")
    app.add_middleware(PrometheusMiddleware)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        retryable = exc.status_code in {429, 503, 504}
        trace_id = getattr(request.state, "trace_id", "trace_unknown")
        code_map = {
            400: "INVALID_ARGUMENT",
            401: "UNAUTHENTICATED",
            403: "PERMISSION_DENIED",
            404: "NOT_FOUND",
            409: "CONFLICT",
            429: "RATE_LIMITED",
            503: "DEPENDENCY_UNAVAILABLE",
            504: "TIMEOUT",
        }
        payload = {
            "error": {
                "code": code_map.get(exc.status_code, "UNKNOWN"),
                "message": str(exc.detail),
                "retryable": retryable,
                "request_id": request.headers.get("X-Request-Id", "req_unknown"),
                "trace_id": trace_id,
            }
        }
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):  # noqa: ANN001
        trace_id = getattr(request.state, "trace_id", "trace_unknown")
        payload = {
            "error": {
                "code": "INTERNAL",
                "message": str(exc),
                "retryable": False,
                "request_id": request.headers.get("X-Request-Id", "req_unknown"),
                "trace_id": trace_id,
            }
        }
        return JSONResponse(status_code=500, content=payload)

    app.include_router(routes_health.router)
    app.include_router(routes_admin.router)
    app.include_router(routes_personal.router)
    app.include_router(routes_analytics.router)
    app.include_router(routes_suggest.router)

    @app.get("/")
    def root() -> dict:
        return {"service": "ocg-api", "version": "1.0.0"}

    return app


app = create_app()
