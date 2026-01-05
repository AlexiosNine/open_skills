"""Utility functions for Skill Host."""

import json
import logging
import time
from typing import Any, Dict, Optional


class TraceIDFormatter(logging.Formatter):
    """Custom formatter that ensures trace_id is always present."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record, ensuring trace_id exists."""
        # Ensure trace_id exists before formatting
        if not hasattr(record, "trace_id") or record.trace_id is None or record.trace_id == "":
            record.trace_id = "-"
        return super().format(record)


def setup_logging(debug: bool = False) -> None:
    """
    Setup logging configuration.

    Args:
        debug: Enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO
    
    # Use a format that includes trace_id
    format_str = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(trace_id)s] - %(message)s"
    )

    # Get root logger
    root_logger = logging.getLogger()
    
    # Create filter instance (shared across handlers)
    trace_filter = TraceIDFilter()
    
    # Only configure if not already configured
    if not root_logger.handlers:
        # Create a handler
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Use custom formatter that ensures trace_id exists
        formatter = TraceIDFormatter(format_str)
        handler.setFormatter(formatter)
        
        # Add filter to handler as well (double protection)
        handler.addFilter(trace_filter)
        
        root_logger.setLevel(level)
        root_logger.addHandler(handler)
    else:
        # Update existing handlers
        for handler in root_logger.handlers:
            # Update formatter to use TraceIDFormatter
            if not isinstance(handler.formatter, TraceIDFormatter):
                handler.setFormatter(TraceIDFormatter(format_str))
            # Add filter if not present
            if not any(isinstance(f, TraceIDFilter) for f in handler.filters):
                handler.addFilter(trace_filter)
        
        # Also add to logger filters as backup
        if not any(isinstance(f, TraceIDFilter) for f in root_logger.filters):
            root_logger.addFilter(trace_filter)
    
    # Ensure all child loggers also get the filter
    # This is important for modules that create their own loggers
    # and for uvicorn's multiprocessing environment
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        child_logger = logging.getLogger(logger_name)
        if child_logger is not root_logger:
            # Update handlers
            for handler in child_logger.handlers:
                if not isinstance(handler.formatter, TraceIDFormatter):
                    handler.setFormatter(TraceIDFormatter(format_str))
                if not any(isinstance(f, TraceIDFilter) for f in handler.filters):
                    handler.addFilter(trace_filter)
            # Add to logger filters
            if not any(isinstance(f, TraceIDFilter) for f in child_logger.filters):
                child_logger.addFilter(trace_filter)


class TraceIDFilter(logging.Filter):
    """Logging filter to add trace_id to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add trace_id to log record if available."""
        # Always ensure trace_id exists, default to "-"
        # Use getattr with default to safely check
        record.trace_id = getattr(record, "trace_id", "-")
        if record.trace_id is None or record.trace_id == "":
            record.trace_id = "-"
        return True


def safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string.

    Args:
        text: JSON string to parse

    Returns:
        Parsed dict or None if parsing fails
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def format_latency_ms(start_time: float) -> int:
    """
    Calculate latency in milliseconds.

    Args:
        start_time: Start time from time.time()

    Returns:
        Latency in milliseconds
    """
    return int((time.time() - start_time) * 1000)


def sanitize_path(path: str) -> str:
    """
    Sanitize file path for logging (remove sensitive info).

    Args:
        path: File path

    Returns:
        Sanitized path
    """
    # Replace home directory with ~
    import os
    home = os.path.expanduser("~")
    if path.startswith(home):
        return path.replace(home, "~", 1)
    return path


def truncate_string(text: str, max_length: int = 200) -> str:
    """
    Truncate string to max length.

    Args:
        text: String to truncate
        max_length: Maximum length

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_version() -> str:
    """Get application version."""
    try:
        from . import __version__
        return __version__
    except ImportError:
        return "0.1.0"

