"""Pydantic schema for file_search skill."""

from typing import Optional

from pydantic import BaseModel, Field


class FileSearchInput(BaseModel):
    """Input schema for file_search skill."""

    query: str = Field(..., description="Search query string")
    root_dir: Optional[str] = Field(
        None, description="Root directory to search (default: ./data)"
    )
    glob: Optional[str] = Field(None, description="Glob pattern for file matching")
    limit: Optional[int] = Field(20, description="Maximum number of results")

