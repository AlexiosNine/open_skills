"""Data models for Agent."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Message role: user, assistant, or tool")
    content: str = Field(..., description="Message content")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None, description="Tool calls from assistant"
    )
    tool_call_id: Optional[str] = Field(
        None, description="Tool call ID for tool role messages"
    )
    name: Optional[str] = Field(None, description="Tool name for tool role messages")


class ToolCall(BaseModel):
    """Tool call request model."""

    id: Optional[str] = Field(None, description="Tool call ID")
    name: str = Field(..., description="Tool/skill name")
    arguments: Dict[str, Any] = Field(..., description="Tool call arguments")


class ToolResult(BaseModel):
    """Tool execution result."""

    tool_call_id: Optional[str] = None
    tool_name: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LLMResponse(BaseModel):
    """LLM response model."""

    content: Optional[str] = Field(None, description="Text response")
    tool_calls: Optional[List[ToolCall]] = Field(
        None, description="Tool calls requested by LLM"
    )
    finish_reason: str = Field(
        ..., description="Finish reason: stop, tool_calls, length, etc."
    )
    usage: Optional[Dict[str, int]] = Field(
        None, description="Token usage: prompt_tokens, completion_tokens, total_tokens"
    )


class ValidationResult(BaseModel):
    """Tool call validation result."""

    valid: bool
    error_message: Optional[str] = None
    corrected_arguments: Optional[Dict[str, Any]] = None


class AgentRequest(BaseModel):
    """Agent chat request."""

    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for multi-turn chat"
    )
    provider: str = Field(
        "openai", description="LLM provider: openai, qwen"
    )
    model: Optional[str] = Field(None, description="Model name (optional, uses default if not provided)")
    max_tool_calls: int = Field(5, ge=1, le=10, description="Maximum tool calls per request")
    max_tokens: int = Field(2000, ge=100, le=8000, description="Maximum tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature")
    max_validation_retries: int = Field(
        3, ge=0, le=5, description="Maximum validation retry attempts"
    )


class AgentResponse(BaseModel):
    """Agent chat response."""

    success: bool
    response: str = Field(..., description="Final response from agent")
    conversation_id: str = Field(..., description="Conversation ID")
    trace_id: str = Field(..., description="Trace ID")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tool calls made during conversation"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata: provider, model, tokens, latency, etc.",
    )

