"""Middleware for FastAPI application."""

import logging
import time
from typing import Callable

from fastapi import Request, Response

logger = logging.getLogger(__name__)

# Ensure trace_id is available for middleware logs
def _ensure_trace_id(record: logging.LogRecord) -> None:
    """Ensure trace_id exists in log record."""
    if not hasattr(record, "trace_id") or record.trace_id is None:
        record.trace_id = "-"


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log requests and responses.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response
    """
    start_time = time.time()

    # Log request
    logger.debug(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )

    # Process request
    response = await call_next(request)

    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # Log response
    logger.debug(
        f"Response: {response.status_code} ({latency_ms}ms)",
        extra={
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "path": request.url.path,
        },
    )

    # Add latency header
    response.headers["X-Process-Time-Ms"] = str(latency_ms)

    return response

