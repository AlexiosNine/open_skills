"""Middleware for FastAPI application."""

import logging
import time
import uuid
from typing import Callable
from contextvars import ContextVar

from fastapi import Request, Response

logger = logging.getLogger(__name__)

# Context variable for trace_id (imported from app.py pattern)
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")

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
    
    # Extract trace_id from header or generate new one
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    trace_id_ctx.set(trace_id)
    
    # Record request body size (if available)
    request_body_size = None
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            request_body_size = int(content_length)
        except ValueError:
            pass

    # Log request
    logger.debug(
        f"Request: {request.method} {request.url.path}",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
            "body_size": request_body_size,
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
            "trace_id": trace_id,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "path": request.url.path,
        },
    )

    # Add latency and trace_id headers
    response.headers["X-Process-Time-Ms"] = str(latency_ms)
    response.headers["X-Trace-Id"] = trace_id

    return response

