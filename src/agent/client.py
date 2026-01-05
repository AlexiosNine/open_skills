"""LLM Client - supports OpenAI and DashScope/Qwen."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..config import config
from .models import LLMResponse, Message, ToolCall

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Chat with LLM.

        Args:
            messages: Conversation messages
            tools: Available tools (Function Calling schemas)
            max_tokens: Maximum tokens
            temperature: Temperature

        Returns:
            LLMResponse
        """
        pass

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """Check if this client supports function calling."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )

        self.client = openai.OpenAI(
            api_key=api_key or config.openai_api_key,
            base_url=config.openai_api_base if config.openai_api_base != "https://api.openai.com/v1" else None,
        )
        self.model = model or config.openai_model

        if not self.client.api_key:
            raise ValueError("OpenAI API key is required")

    def supports_function_calling(self) -> bool:
        return True

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Chat with OpenAI."""
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            message_dict = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                message_dict["name"] = msg.name
            openai_messages.append(message_dict)

        # Prepare tools
        openai_tools = None
        if tools:
            openai_tools = tools

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=openai_tools,
                tool_choice="auto" if tools else None,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            choice = response.choices[0]
            message = choice.message

            # Extract tool calls
            tool_calls = None
            if message.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=self._parse_arguments(tc.function.arguments),
                    )
                    for tc in message.tool_calls
                ]

            return LLMResponse(
                content=message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise

    def _parse_arguments(self, arguments: str) -> Dict[str, Any]:
        """Parse JSON arguments string."""
        import json

        try:
            return json.loads(arguments)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool arguments: {e}")
            return {}


class QwenClient(LLMClient):
    """DashScope/Qwen API client."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        try:
            import dashscope
        except ImportError:
            raise ImportError(
                "dashscope package is required. Install with: pip install dashscope"
            )

        self.api_key = api_key or config.dashscope_api_key
        self.model = model or config.dashscope_model
        dashscope.api_key = self.api_key

        if not self.api_key:
            raise ValueError("DashScope API key is required")

    def supports_function_calling(self) -> bool:
        return True

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Chat with Qwen."""
        import dashscope
        from dashscope import Generation

        # Convert messages to Qwen format
        qwen_messages = []
        for msg in messages:
            message_dict = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                message_dict["name"] = msg.name
            qwen_messages.append(message_dict)

        # Prepare tools
        qwen_tools = None
        if tools:
            # Qwen uses similar format to OpenAI
            qwen_tools = tools

        try:
            response = Generation.call(
                model=self.model,
                messages=qwen_messages,
                tools=qwen_tools,
                result_format="message",
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if response.status_code != 200:
                raise Exception(f"Qwen API error: {response.message}")

            output = response.output
            message = output.choices[0].message

            # Extract tool calls
            # Qwen returns message as dict or object
            tool_calls = None
            try:
                message_dict = message if isinstance(message, dict) else message.__dict__ if hasattr(message, "__dict__") else {}
                
                if "tool_calls" in message_dict and message_dict["tool_calls"]:
                    tool_calls_list = message_dict["tool_calls"]
                    tool_calls = [
                        ToolCall(
                            id=tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None),
                            name=tc["function"]["name"] if isinstance(tc, dict) else tc.function.name if hasattr(tc, "function") else None,
                            arguments=self._parse_arguments(
                                tc["function"]["arguments"] if isinstance(tc, dict) else tc.function.arguments if hasattr(tc, "function") else {}
                            ),
                        )
                        for tc in tool_calls_list
                    ]
                elif hasattr(message, "tool_calls") and message.tool_calls:
                    # Handle as object
                    tool_calls = [
                        ToolCall(
                            id=getattr(tc, "id", None),
                            name=getattr(tc.function, "name", None) if hasattr(tc, "function") else None,
                            arguments=self._parse_arguments(
                                getattr(tc.function, "arguments", {}) if hasattr(tc, "function") else {}
                            ),
                        )
                        for tc in message.tool_calls
                    ]
            except (KeyError, AttributeError, TypeError) as e:
                logger.warning(f"Failed to extract tool_calls from Qwen response: {e}")
                tool_calls = None

            # Extract content
            content = None
            try:
                if isinstance(message, dict):
                    content = message.get("content")
                elif hasattr(message, "content"):
                    content = message.content
            except Exception as e:
                logger.warning(f"Failed to extract content from Qwen response: {e}")
                content = None

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=output.choices[0].finish_reason or "stop",
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if hasattr(response, "usage") and response.usage
                else None,
            )
        except Exception as e:
            logger.error(f"Qwen API error: {e}", exc_info=True)
            raise

    def _parse_arguments(self, arguments: Any) -> Dict[str, Any]:
        """Parse arguments (could be dict or JSON string)."""
        import json

        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, str):
            try:
                return json.loads(arguments)
            except json.JSONDecodeError:
                return {}
        return {}


def create_client(provider: str, model: Optional[str] = None) -> LLMClient:
    """
    Create LLM client based on provider.

    Args:
        provider: Provider name (openai, qwen)
        model: Optional model name override

    Returns:
        LLMClient instance
    """
    if provider == "openai":
        return OpenAIClient(model=model)
    elif provider == "qwen":
        return QwenClient(model=model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

