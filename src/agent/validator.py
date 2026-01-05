"""Pydantic validator for tool call arguments."""

import logging
from typing import Any, Dict

from pydantic import ValidationError

from .models import ToolCall, ValidationResult
from .schemas import SKILL_INPUT_SCHEMAS

logger = logging.getLogger(__name__)


class ToolCallValidator:
    """Validates tool call arguments using Pydantic models."""

    def validate(self, tool_call: ToolCall) -> ValidationResult:
        """
        Validate tool call arguments.

        Args:
            tool_call: ToolCall object

        Returns:
            ValidationResult
        """
        schema_class = SKILL_INPUT_SCHEMAS.get(tool_call.name)

        if not schema_class:
            return ValidationResult(
                valid=False,
                error_message=f"Unknown tool: {tool_call.name}",
            )

        try:
            # Validate arguments
            validated_data = schema_class(**tool_call.arguments)
            return ValidationResult(
                valid=True,
                corrected_arguments=validated_data.model_dump(exclude_none=True),
            )
        except ValidationError as e:
            error_message = self._format_validation_error(e, tool_call.name)
            return ValidationResult(
                valid=False,
                error_message=error_message,
            )

    def _format_validation_error(
        self, error: ValidationError, tool_name: str
    ) -> str:
        """
        Format Pydantic validation error for LLM feedback.

        Args:
            error: ValidationError from Pydantic
            tool_name: Tool name

        Returns:
            Formatted error message
        """
        errors = []
        for err in error.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            error_type = err["type"]
            error_msg = err["msg"]

            # Format error message
            if error_type == "missing":
                errors.append(f"- {field}: 字段是必需的（缺失）")
            elif error_type == "type_error":
                errors.append(
                    f"- {field}: 类型错误 - {error_msg}（当前值: {err.get('input', 'N/A')}）"
                )
            elif error_type == "value_error":
                errors.append(f"- {field}: 值错误 - {error_msg}")
            else:
                errors.append(f"- {field}: {error_msg}")

        error_message = f"""工具调用参数格式错误：
工具名称: {tool_name}
错误详情:
{chr(10).join(errors)}

请根据以上错误修正参数格式，确保：
1. 所有必需字段都已提供
2. 字段类型正确
3. 参数值符合约束条件

请修正参数后重试。"""

        return error_message

