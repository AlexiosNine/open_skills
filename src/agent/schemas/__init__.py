"""Pydantic schemas for skill input/output validation."""

from .echo import EchoInput
from .file_search import FileSearchInput
from .calculator import CalculatorInput
from .log_transform import LogTransformInput

__all__ = [
    "EchoInput",
    "FileSearchInput",
    "CalculatorInput",
    "LogTransformInput",
]

# Mapping from skill_id to input schema class
SKILL_INPUT_SCHEMAS = {
    "echo": EchoInput,
    "file_search": FileSearchInput,
    "calculator": CalculatorInput,
    "log_transform": LogTransformInput,
}

