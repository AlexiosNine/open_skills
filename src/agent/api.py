"""FastAPI routes for Agent."""

import logging
import uuid

from fastapi import APIRouter, HTTPException, Header

from .agent import get_agent
from .models import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

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

    # Validate provider
    if request.provider not in ("openai", "qwen"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {request.provider}. Supported: openai, qwen",
        )

    # Get agent and chat
    # Run in thread pool to avoid blocking event loop
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    agent = get_agent()
    
    try:
        # Use thread pool to run synchronous agent.chat() to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
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

