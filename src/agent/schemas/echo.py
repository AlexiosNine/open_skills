"""Pydantic schema for echo skill."""

from pydantic import BaseModel, Field


class EchoInput(BaseModel):
    """Input schema for echo skill."""

    text: str = Field(..., description="Text to echo back")

