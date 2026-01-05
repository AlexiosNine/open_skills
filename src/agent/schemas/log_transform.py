"""Pydantic schema for log_transform skill."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LogTransformInput(BaseModel):
    """Input schema for log_transform skill."""

    input_path: str = Field(..., description="Path to log file (must be under ./data)")
    format: Optional[str] = Field(
        "text", description="Input format: text, jsonl"
    )
    output: Optional[str] = Field(
        "stdout", description="Output destination: stdout, file"
    )
    rules: Optional[Dict[str, Any]] = Field(
        None,
        description="Transformation rules: timestamp_regex, level_map, etc.",
    )
    limit: Optional[int] = Field(200, description="Maximum number of records to process")

