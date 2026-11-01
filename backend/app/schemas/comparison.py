from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    scheme_ids: List[str] = Field(..., min_length=2, max_length=5, example=["PM-KISAN", "PM-USP-CSSS"])


class ComparisonMatrixRow(BaseModel):
    attribute: str
    values: Dict[str, Any]


class CompareResponse(BaseModel):
    scheme_ids: List[str]
    schemes: List[Dict[str, Any]]
    comparison_matrix: List[ComparisonMatrixRow]
    total_compared: int
