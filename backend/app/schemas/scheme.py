from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SchemeBase(BaseModel):
    scheme_id: str = Field(..., example="PM-KISAN")
    scheme_name: str = Field(..., example="Pradhan Mantri Kisan Samman Nidhi")
    category: str = Field(..., example="Agriculture")
    ministry: str = Field(..., example="Ministry of Agriculture and Farmers Welfare")
    level: str = Field("Central", example="Central")
    source: str = Field(..., example="PM-KISAN")
    official_url: str = Field(..., example="https://www.pmkisan.gov.in/")


class SchemeDetail(SchemeBase):
    helpline: Optional[str] = None
    description: Optional[str] = None
    financial_assistance: Optional[str] = None
    benefits: List[str] = []
    eligibility_summary: Optional[str] = None
    eligibility_criteria: Dict[str, Any] = {}
    exclusions: List[str] = []
    documents_required: List[str] = []
    how_to_apply: Optional[str] = None


class SchemeListResponse(BaseModel):
    total: int
    schemes: List[SchemeDetail]
