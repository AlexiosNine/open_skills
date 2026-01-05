"""Pydantic schema for calculator skill."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    """Input schema for calculator skill."""

    numbers: List[float] = Field(..., description="List of numbers to calculate")
    ops: List[str] = Field(
        ...,
        description="Operations to perform: mean, median, min, max, sum",
    )
    compare: Optional[Dict[str, float]] = Field(
        None, description="Comparison values: {'a': 10, 'b': 12}"
    )

