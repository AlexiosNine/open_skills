"""Security utilities for path validation."""

from pathlib import Path
from typing import Optional

from .config import config


class SecurityError(Exception):
    """Security-related error."""

    pass


def validate_path(
    path: str, allowed_root: Optional[Path] = None
) -> Path:
    """
    Validate that a path is within the allowed root directory.

    Args:
        path: The path to validate (can be relative or absolute)
        allowed_root: The allowed root directory (defaults to config.allowed_root)

    Returns:
        Resolved Path object if valid

    Raises:
        SecurityError: If the path is invalid or outside allowed root
    """
    if allowed_root is None:
        allowed_root = config.allowed_root

    # Convert to Path
    input_path = Path(path)

    # Reject absolute paths (recommended)
    if input_path.is_absolute():
        raise SecurityError(
            f"Absolute paths are not allowed: {path}"
        )

    # Reject paths containing '..'
    if ".." in path:
        raise SecurityError(
            f"Path traversal ('..') is not allowed: {path}"
        )

    # Resolve the path relative to current working directory
    try:
        resolved = input_path.resolve()
    except Exception as e:
        raise SecurityError(f"Failed to resolve path: {path}") from e

    # Ensure resolved path is within allowed_root
    try:
        resolved.relative_to(allowed_root.resolve())
    except ValueError:
        raise SecurityError(
            f"Path is outside allowed root ({allowed_root}): {resolved}"
        )

    return resolved


def ensure_within_allowed_root(path: Path) -> Path:
    """
    Ensure a Path object is within the allowed root.

    Args:
        path: The path to check

    Returns:
        The path if valid

    Raises:
        SecurityError: If the path is outside allowed root
    """
    allowed_root = config.allowed_root.resolve()
    try:
        path.resolve().relative_to(allowed_root)
    except ValueError:
        raise SecurityError(
            f"Path is outside allowed root ({allowed_root}): {path}"
        )
    return path

