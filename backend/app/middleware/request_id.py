import time
import uuid
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("taxpulse.request")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

SENSITIVE_PARAM_NAMES = {"key", "token", "secret", "password", "api_key", "authorization", "x-goog-api-key"}


def sanitize_url(request: Request) -> str:
    query_params = []
    for key, value in request.query_params.items():
        if key.lower() in SENSITIVE_PARAM_NAMES:
            query_params.append(f"{key}=[REDACTED]")
        else:
            query_params.append(f"{key}={value}")
    query_str = f"?{'&'.join(query_params)}" if query_params else ""
    return f"{request.url.path}{query_str}"


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        sanitized_path = sanitize_url(request)

        # Process request
        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Request-ID"] = request_id

        # Log request without leaking secrets
        logger.info(
            f"req_id={request_id} method={request.method} path={sanitized_path} "
            f"status={response.status_code} duration={duration_ms:.2f}ms"
        )

        return response
