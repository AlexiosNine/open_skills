"""FastAPI Skill Host application."""

import logging
import re
import time
import uuid

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from .config import config
from .models import (
    ErrorCode,
    ErrorDetail,
    NormalizedSkillResult,
    SkillInvokeRequest,
)
from .agent.api import router as agent_router
from .middleware import logging_middleware, trace_id_ctx
from .registry import get_registry
from .runners import get_factory
from .utils import format_latency_ms, get_version, setup_logging

# Setup logging
setup_logging(debug=config.debug)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OpenSkill Skill Host",
    description="Local Skill Host for executing skills via unified HTTP protocol",
    version=get_version(),
    tags_metadata=[
        {
            "name": "skills",
            "description": "Skill invocation endpoints",
        },
        {
            "name": "system",
            "description": "System information endpoints",
        },
    ],
)

# Add middleware
app.middleware("http")(logging_middleware)

# Include agent routes
app.include_router(agent_router)


def _get_trace_id(x_trace_id: str | None = None) -> str:
    """Get or generate trace ID."""
    if x_trace_id and x_trace_id.strip():
        return x_trace_id.strip()
    return str(uuid.uuid4())


@app.get("/", tags=["system"])
async def root():
    """Root endpoint - list available skills."""
    registry = get_registry()
    return {
        "service": "OpenSkill Skill Host",
        "version": get_version(),
        "skills": registry.list_skills(),
        "llm_providers": config.get_llm_providers() if config.has_llm_config() else [],
    }


@app.get("/health", tags=["system"])
async def health():
    """Health check endpoint."""
    registry = get_registry()
    return {
        "status": "ok",
        "skills_count": len(registry.list_skills()),
        "llm_configured": config.has_llm_config(),
    }


@app.post("/skills/{skill_id}:invoke", tags=["skills"])
async def invoke_skill(
    skill_id: str,
    request: SkillInvokeRequest,
    x_trace_id: str | None = Header(None, alias="X-Trace-Id"),
) -> NormalizedSkillResult:
    """
    Invoke a skill.

    Args:
        skill_id: The skill ID
        request: The invocation request
        x_trace_id: Optional trace ID from header

    Returns:
        NormalizedSkillResult
    """
    # Validate skill_id format (alphanumeric and hyphens only)
    import re
    if not re.match(r"^[a-z0-9-]+$", skill_id):
        latency_ms = format_latency_ms(time.time())
        return NormalizedSkillResult(
            success=False,
            skill_id=skill_id,
            trace_id=_get_trace_id(x_trace_id),
            data=None,
            error=ErrorDetail(
                code=ErrorCode.INVALID_ARGUMENT,
                message=f"Invalid skill_id format: {skill_id}. Only lowercase letters, numbers, and hyphens are allowed.",
            ),
            meta={"latency_ms": latency_ms, "version": get_version()},
        )
    
    start_time = time.time()
    trace_id = _get_trace_id(x_trace_id)
    # trace_id is already set in middleware, but ensure it's set here too for consistency
    trace_id_ctx.set(trace_id)

    logger.info(
        f"Invoking skill: skill_id={skill_id}",
        extra={"trace_id": trace_id},
    )

    # Get registry and factory
    # Note: registry and factory are global singletons, get_registry() and get_factory() just return instances
    registry = get_registry()
    factory = get_factory()

    # Get skill manifest
    manifest = registry.get_skill(skill_id)
    if not manifest:
        latency_ms = format_latency_ms(start_time)
        result = NormalizedSkillResult(
            success=False,
            skill_id=skill_id,
            trace_id=trace_id,
            data=None,
            error=ErrorDetail(
                code=ErrorCode.NOT_FOUND,
                message=f"Skill not found: {skill_id}",
            ),
            meta={"latency_ms": latency_ms, "version": get_version()},
        )
        logger.warning(
            f"Skill not found: skill_id={skill_id}",
            extra={"trace_id": trace_id},
        )
        return result

    # Get runner
    try:
        runner = factory.get_runner(manifest)
    except ValueError as e:
        latency_ms = format_latency_ms(start_time)
        result = NormalizedSkillResult(
            success=False,
            skill_id=skill_id,
            trace_id=trace_id,
            data=None,
            error=ErrorDetail(
                code=ErrorCode.INTERNAL,
                message=f"Failed to get runner: {str(e)}",
            ),
            meta={"latency_ms": latency_ms, "version": get_version()},
        )
        logger.error(
            f"Failed to get runner: skill_id={skill_id}, error={e}",
            extra={"trace_id": trace_id},
            exc_info=True,
        )
        return result

    # Invoke the skill
    result = None
    try:
        result = runner.invoke(
            skill_id=skill_id,
            input_data=request.input,
            trace_id=trace_id,
            manifest=manifest,
        )
    except Exception as e:
        latency_ms = format_latency_ms(start_time)
        result = NormalizedSkillResult(
            success=False,
            skill_id=skill_id,
            trace_id=trace_id,
            data=None,
            error=ErrorDetail(
                code=ErrorCode.INTERNAL,
                message="Unexpected error during skill invocation",
                details={"exception": type(e).__name__, "reason": str(e)},
            ),
            meta={"latency_ms": latency_ms, "version": get_version()},
        )
        logger.error(
            f"Unexpected error invoking skill: skill_id={skill_id}, error={e}",
            extra={"trace_id": trace_id},
            exc_info=True,
        )

    # Ensure result is not None (safety check)
    if result is None:
        latency_ms = format_latency_ms(start_time)
        result = NormalizedSkillResult(
            success=False,
            skill_id=skill_id,
            trace_id=trace_id,
            data=None,
            error=ErrorDetail(
                code=ErrorCode.INTERNAL,
                message="Skill invocation returned no result",
            ),
            meta={"latency_ms": latency_ms, "version": get_version()},
        )
        logger.error(
            f"Skill invocation returned None: skill_id={skill_id}",
            extra={"trace_id": trace_id},
        )

    # Log the result
    latency_ms = result.meta.latency_ms if result.meta else 0
    logger.info(
        f"Skill invocation completed: skill_id={skill_id}, success={result.success}, "
        f"latency_ms={latency_ms}",
        extra={"trace_id": trace_id, "skill_id": skill_id, "success": result.success},
    )

    return result


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    # Extract trace_id from request header if available
    trace_id = request.headers.get("X-Trace-Id") or _get_trace_id()
    
    # In production, don't expose detailed exception information
    include_details = config.debug
    error_details = None
    if include_details:
        error_details = {"exception": type(exc).__name__, "reason": str(exc)}
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True, extra={"trace_id": trace_id})
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "skill_id": "unknown",
            "trace_id": trace_id,
            "data": None,
            "error": {
                "code": ErrorCode.INTERNAL.value,
                "message": "Internal server error",
                "details": error_details,
            },
            "meta": {"latency_ms": 0, "version": get_version()},
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app:app",
        host="127.0.0.1",
        port=8000,
        reload=config.debug,
    )

