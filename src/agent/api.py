"""FastAPI routes for Agent."""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Header

from ..config import config
from .agent import get_agent
from .models import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

# Global thread pool executor (reused across requests)
_executor: ThreadPoolExecutor | None = None


def get_executor() -> ThreadPoolExecutor:
    """Get global thread pool executor."""
    global _executor
    if _executor is None:
        max_workers = 10  # Configurable if needed
        _executor = ThreadPoolExecutor(max_workers=max_workers)
    return _executor

# Create router
router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentResponse)
async def chat(
    request: AgentRequest,
    x_trace_id: str | None = Header(None, alias="X-Trace-Id"),
) -> AgentResponse:
    """
    Chat with agent - LLM autonomously calls tools.

    Args:
        request: AgentRequest
        x_trace_id: Optional trace ID from header

    Returns:
        AgentResponse
    """
    trace_id = x_trace_id or str(uuid.uuid4())

    logger.info(
        f"Agent chat request: conversation_id={request.conversation_id}, "
        f"provider={request.provider}, trace_id={trace_id}"
    )

    # Validate provider dynamically from config
    available_providers = config.get_llm_providers()
    if not available_providers:
        raise HTTPException(
            status_code=500,
            detail="No LLM provider configured. Please configure at least one LLM API key.",
        )
    
    # Map provider names (dashscope -> qwen for backward compatibility)
    provider_map = {
        "qwen": "dashscope",
        "openai": "openai",
    }
    actual_provider = provider_map.get(request.provider, request.provider)
    
    if actual_provider not in available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported or unconfigured provider: {request.provider}. "
                   f"Available providers: {', '.join(available_providers)}",
        )

    # Get agent and chat
    # Run in thread pool to avoid blocking event loop
    agent = get_agent()
    executor = get_executor()
    
    try:
        # Use global thread pool to run synchronous agent.chat() to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            executor, 
            lambda: agent.chat(request, trace_id=trace_id)
        )
        return response
    except ValueError as e:
        # Missing API key or configuration error
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        )

