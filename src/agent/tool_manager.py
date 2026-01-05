"""Tool Manager - converts skills to Function Calling schemas."""

import logging
from typing import Any, Dict, List, Optional

from ..registry import get_registry
from .schemas import SKILL_INPUT_SCHEMAS

logger = logging.getLogger(__name__)


class ToolManager:
    """Manages tools and converts them to Function Calling schemas."""

    def __init__(self):
        self.registry = get_registry()
        self._tool_schemas: Optional[List[Dict[str, any]]] = None

    def get_available_tools(self) -> List[Dict[str, any]]:
        """
        Get all available tools as Function Calling schemas.

        Returns:
            List of tool schemas in Function Calling format
        """
        if self._tool_schemas is None:
            self._tool_schemas = self._build_tool_schemas()
        return self._tool_schemas

    def _build_tool_schemas(self) -> List[Dict[str, any]]:
        """Build Function Calling schemas from registered skills."""
        tools = []
        skill_ids = self.registry.list_skills()

        for skill_id in skill_ids:
            manifest = self.registry.get_skill(skill_id)
            if not manifest:
                continue

            tool_schema = self._skill_to_function_schema(manifest)
            if tool_schema:
                tools.append(tool_schema)

        logger.info(f"Built {len(tools)} tool schemas")
        return tools

    def _skill_to_function_schema(
        self, manifest
    ) -> Optional[Dict[str, Any]]:
        """
        Convert SkillManifest to Function Calling schema.

        Args:
            manifest: SkillManifest object

        Returns:
            Function Calling schema dict or None
        """
        # Get input schema class
        input_schema_class = SKILL_INPUT_SCHEMAS.get(manifest.id)
        if not input_schema_class:
            logger.warning(f"No input schema found for skill: {manifest.id}")
            return None

        # Get description from manifest or use default
        description = self._get_skill_description(manifest)

        # Convert Pydantic model to JSON schema
        json_schema = input_schema_class.model_json_schema()

        # Build Function Calling schema
        function_schema = {
            "type": "function",
            "function": {
                "name": manifest.id,
                "description": description,
                "parameters": {
                    "type": json_schema.get("type", "object"),
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                },
            },
        }

        return function_schema

    def _get_skill_description(self, manifest) -> str:
        """Get skill description from various sources."""
        # Try to get from manifest (if we add description field later)
        # For now, use hardcoded descriptions based on skill_id
        descriptions = {
            "echo": "回显输入的文本，用于连通性验证",
            "file_search": "在允许目录（默认 ./data）下检索文件内容并返回命中片段",
            "calculator": "数据处理和统计计算（均值、中位数、最小/最大、比较大小等）",
            "log_transform": "将日志文件转换为结构化记录（JSON/JSONL/CSV等）",
        }

        return descriptions.get(manifest.id, f"Execute {manifest.id} skill")

    def invoke_tool(
        self, tool_name: str, arguments: Dict[str, Any], trace_id: str
    ) -> Dict[str, Any]:
        """
        Invoke a tool directly via Runner (avoid HTTP deadlock).

        Args:
            tool_name: Tool/skill name
            arguments: Tool arguments
            trace_id: Trace ID

        Returns:
            NormalizedSkillResult as dict
        """
        from ..runners import get_factory
        from ..models import NormalizedSkillResult

        # Get skill manifest
        manifest = self.registry.get_skill(tool_name)
        if not manifest:
            return {
                "success": False,
                "skill_id": tool_name,
                "trace_id": trace_id,
                "data": None,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Skill not found: {tool_name}",
                },
                "meta": {"latency_ms": 0, "version": "0.1.0"},
            }

        try:
            # Get runner and invoke directly (avoid HTTP deadlock)
            factory = get_factory()
            runner = factory.get_runner(manifest)
            
            result = runner.invoke(
                skill_id=tool_name,
                input_data=arguments,
                trace_id=trace_id,
                manifest=manifest,
            )
            
            # Convert NormalizedSkillResult to dict
            return {
                "success": result.success,
                "skill_id": result.skill_id,
                "trace_id": result.trace_id,
                "data": result.data,
                "error": {
                    "code": result.error.code.value,
                    "message": result.error.message,
                    "details": result.error.details,
                } if result.error else None,
                "meta": {
                    "latency_ms": result.meta.latency_ms if result.meta else 0,
                    "version": result.meta.version if result.meta else "0.1.0",
                },
            }
        except Exception as e:
            logger.error(f"Failed to invoke tool {tool_name}: {e}", exc_info=True)
            return {
                "success": False,
                "skill_id": tool_name,
                "trace_id": trace_id,
                "data": None,
                "error": {
                    "code": "TOOL_INVOCATION_ERROR",
                    "message": f"Failed to invoke tool: {str(e)}",
                },
                "meta": {"latency_ms": 0, "version": "0.1.0"},
            }

