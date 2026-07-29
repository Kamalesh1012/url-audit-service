import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.audit import router as audit_router
from app.config import settings
from app.models.response import ErrorDetail, HealthResponse
from app.services.analyzer import AnalysisError
from app.services.fetcher import FetchError
from app.utils.logger import configure_logging, log, new_request_id, set_request_id

configure_logging()


def _client_key(request: Request) -> str:
    """Rate-limit by API key if present, else fall back to remote IP."""
    api_key = request.headers.get("x-api-key")
    return api_key or get_remote_address(request)


limiter = Limiter(key_func=_client_key, default_limits=[settings.rate_limit])

app = FastAPI(title=settings.app_name, version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(audit_router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Assign a request ID, bind it to the logger, log entry/exit + latency."""
    request_id = new_request_id()
    set_request_id(request_id)
    request.state.request_id = request_id

    start = time.perf_counter()
    log.info("request_started", path=request.url.path, method=request.method)
    try:
        response = await call_next(request)
    except Exception:
        log.exception("request_unhandled_error", path=request.url.path)
        raise
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Request-ID"] = request_id
    log.info("request_finished", path=request.url.path, status_code=response.status_code, elapsed_ms=elapsed_ms)
    return response


def _service_error_response(request: Request, exc) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "-")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorDetail(error=exc.code, message=exc.message, request_id=request_id).model_dump(),
    )


@app.exception_handler(FetchError)
async def fetch_error_handler(request: Request, exc: FetchError):
    return _service_error_response(request, exc)


@app.exception_handler(AnalysisError)
async def analysis_error_handler(request: Request, exc: AnalysisError):
    return _service_error_response(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "-")
    log.error("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content=ErrorDetail(
            error="internal_error", message="Something went wrong on our end.", request_id=request_id
        ).model_dump(),
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(environment=settings.environment)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "footer_credit": "Built for Digital Heroes Training Task",
        "credit_link": "https://digitalheroesco.com",
    }
