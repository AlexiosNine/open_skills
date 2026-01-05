"""Data models for Skill Host."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Standard error codes."""

    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INVALID_JSON = "INVALID_JSON"
    FORBIDDEN_PATH = "FORBIDDEN_PATH"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    INTERNAL = "INTERNAL"


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None


class SkillMeta(BaseModel):
    """Metadata for skill result."""

    latency_ms: int
    version: str = "0.1.0"
    truncated: Optional[bool] = None


class NormalizedSkillResult(BaseModel):
    """Normalized skill result structure."""

    success: bool
    skill_id: str
    trace_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[ErrorDetail] = None
    meta: Optional[SkillMeta] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "skill_id": "echo",
                "trace_id": "demo-123",
                "data": {"echoed": "hello"},
                "error": None,
                "meta": {"latency_ms": 3, "version": "0.1.0"},
            }
        }


class SkillInvokeRequest(BaseModel):
    """Request structure for skill invocation."""

    input: Dict[str, Any] = Field(..., description="Skill input parameters")


class SkillManifest(BaseModel):
    """Skill manifest definition."""

    id: str
    type: str = "cli"
    runtime: str = "python"
    entry: Optional[str] = None
    timeout_ms: Optional[int] = None
    allowed_root: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "echo",
                "type": "cli",
                "runtime": "python",
                "entry": "./skill_cli/echo.py",
                "timeout_ms": 15000,
                "allowed_root": "./data",
            }
        }

