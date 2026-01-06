"""Agent Loop - manages conversation and tool calling."""

import json
import logging
import time
import uuid
from typing import Dict, List, Optional

from ..config import config
from .client import LLMClient, create_client
from .models import AgentRequest, AgentResponse, Message, ToolCall
from .tool_manager import ToolManager
from .validator import ToolCallValidator

logger = logging.getLogger(__name__)


class Agent:
    """Agent that uses LLM to autonomously call tools."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.tool_manager = ToolManager()
        self.validator = ToolCallValidator()
        self.llm_client = llm_client
        # Conversation storage (in-memory, simple implementation)
        self._conversations: Dict[str, List[Message]] = {}

    def chat(self, request: AgentRequest, trace_id: Optional[str] = None) -> AgentResponse:
        """
        Chat with agent.

        Args:
            request: AgentRequest
            trace_id: Optional trace ID

        Returns:
            AgentResponse
        """
        start_time = time.time()
        trace_id = trace_id or str(uuid.uuid4())
        conversation_id = request.conversation_id or f"conv-{uuid.uuid4()}"

        # Get or create LLM client
        if not self.llm_client:
            self.llm_client = create_client(request.provider, request.model)

        # Get conversation history
        messages = self._get_conversation(conversation_id)

        # Add user message
        messages.append(Message(role="user", content=request.message))

        # Get available tools
        tools = self.tool_manager.get_available_tools()

        # Track tool calls
        tool_calls_made = []
        validation_retries = 0
        total_tokens = 0
        tool_call_count = 0

        # Agent loop
        max_iterations = request.max_tool_calls + 1  # +1 for final response
        for iteration in range(max_iterations):
            # Check token limit
            if total_tokens > 0 and total_tokens >= request.max_tokens:
                logger.warning(f"Token limit reached: {total_tokens}/{request.max_tokens}")
                break

            # Call LLM
            try:
                remaining_tokens = request.max_tokens - total_tokens if total_tokens > 0 else request.max_tokens
                if remaining_tokens <= 0:
                    logger.warning(f"No tokens remaining: {total_tokens}/{request.max_tokens}")
                    break
                llm_response = self.llm_client.chat(
                    messages=messages,
                    tools=tools if iteration < request.max_tool_calls else None,
                    max_tokens=remaining_tokens,
                    temperature=request.temperature,
                )
            except Exception as e:
                logger.error(f"LLM API error: {e}", exc_info=True)
                return AgentResponse(
                    success=False,
                    response=f"LLM API error: {str(e)}",
                    conversation_id=conversation_id,
                    trace_id=trace_id,
                    tool_calls=tool_calls_made,
                    meta={
                        "error": str(e),
                        "latency_ms": int((time.time() - start_time) * 1000),
                    },
                )

            # Track tokens
            if llm_response.usage:
                total_tokens += llm_response.usage.get("total_tokens", 0)

            # Add assistant response to history
            tool_calls_list = None
            if llm_response.tool_calls:
                tool_calls_list = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        },
                    }
                    for tc in llm_response.tool_calls
                ]
            
            assistant_msg = Message(
                role="assistant",
                content=llm_response.content or "",
                tool_calls=tool_calls_list,
            )
            messages.append(assistant_msg)

            # Check if LLM wants to call tools
            if llm_response.tool_calls:
                tool_call_count += len(llm_response.tool_calls)
                has_validation_error = False

                for tool_call in llm_response.tool_calls:
                    # Validate tool call
                    validation_result = self.validator.validate(tool_call)

                    if not validation_result.valid:
                        # Format error and feedback to LLM
                        validation_retries += 1
                        if validation_retries > request.max_validation_retries:
                            logger.warning(
                                f"Max validation retries reached for tool: {tool_call.name}"
                            )
                            error_msg = f"工具调用参数格式错误，已达到最大重试次数。错误: {validation_result.error_message}"
                            messages.append(
                                Message(
                                    role="user",
                                    content=error_msg,
                                )
                            )
                            has_validation_error = True
                            break

                        # Feedback error to LLM
                        logger.info(
                            f"Tool call validation failed, retrying: {tool_call.name}"
                        )
                        messages.append(
                            Message(
                                role="user",
                                content=validation_result.error_message,
                            )
                        )
                        has_validation_error = True
                        break  # Break to retry with LLM

                    # Execute tool call
                    logger.info(
                        f"Executing tool: {tool_call.name} with args: {tool_call.arguments}"
                    )

                    # Use corrected arguments if available
                    arguments = (
                        validation_result.corrected_arguments
                        if validation_result.corrected_arguments
                        else tool_call.arguments
                    )

                    tool_result = self.tool_manager.invoke_tool(
                        tool_call.name, arguments, trace_id
                    )

                    # Record tool call
                    tool_calls_made.append(
                        {
                            "tool": tool_call.name,
                            "arguments": arguments,
                            "validated": True,
                            "result": tool_result,
                        }
                    )

                    # Add tool result to conversation
                    # Format tool result as JSON string for LLM
                    result_content = json.dumps(
                        tool_result.get("data") or tool_result.get("error", {}),
                        ensure_ascii=False,
                    )
                    tool_result_msg = Message(
                        role="tool",
                        content=result_content,
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                    )
                    messages.append(tool_result_msg)

                # If validation error, retry this iteration
                if has_validation_error:
                    continue

                # Continue loop to process tool results
                continue

            # No tool calls, LLM returned final answer
            if llm_response.finish_reason in ("stop", "length"):
                break

        # Save conversation
        self._save_conversation(conversation_id, messages)

        # Build response
        final_response = messages[-1].content if messages else "No response generated"

        latency_ms = int((time.time() - start_time) * 1000)

        return AgentResponse(
            success=True,
            response=final_response,
            conversation_id=conversation_id,
            trace_id=trace_id,
            tool_calls=tool_calls_made,
            meta={
                "provider": request.provider,
                "model": request.model or (self.llm_client.model if hasattr(self.llm_client, "model") else "unknown"),
                "total_tokens": total_tokens,
                "tool_calls_count": tool_call_count,
                "validation_retries": validation_retries,
                "latency_ms": latency_ms,
            },
        )

    def _get_conversation(self, conversation_id: str) -> List[Message]:
        """Get conversation history."""
        return self._conversations.get(conversation_id, [])

    def _save_conversation(self, conversation_id: str, messages: List[Message]) -> None:
        """Save conversation history."""
        # Limit conversation length (keep last 20 messages)
        max_messages = 20
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
        self._conversations[conversation_id] = messages


# Global agent instance
_agent: Optional[Agent] = None


def get_agent() -> Agent:
    """Get global agent instance."""
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent

