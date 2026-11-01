from typing import List, Optional
from pydantic import BaseModel, Field


class EligibilityProfile(BaseModel):
    age: Optional[int] = Field(None, ge=1, le=120, example=25)
    annual_income: Optional[float] = Field(None, ge=0, example=250000.0)
    occupation: Optional[str] = Field(None, example="farmer")
    is_landholding_farmer: Optional[bool] = Field(None, example=True)
    is_institutional_landholder: Optional[bool] = Field(False, example=False)
    is_income_tax_payer: Optional[bool] = Field(False, example=False)
    is_constitutional_post_holder: Optional[bool] = Field(False, example=False)
    is_government_employee: Optional[bool] = Field(False, example=False)
    is_student: Optional[bool] = Field(None, example=False)
    education_level: Optional[str] = Field(None, example="undergraduate")
    class_12_percentile: Optional[float] = Field(None, ge=0.0, le=100.0, example=85.5)
    is_regular_course: Optional[bool] = Field(True, example=True)
    is_technical_degree_or_diploma: Optional[bool] = Field(None, example=False)
    is_aicte_approved_institution: Optional[bool] = Field(None, example=False)
    special_category: Optional[str] = Field(
        "none",
        example="none",
        description="One of: none, orphan, covid_deceased_parents, martyred_armed_forces_ward"
    )
    scheme_id: Optional[str] = Field(None, example="PM-KISAN")
    # New fields for the 10 added schemes (all optional; None = not supplied,
    # so the checker reports them as missing info, never as a silent pass)
    gender: Optional[str] = Field(None, example="female")
    has_bank_account: Optional[bool] = Field(None, example=True)
    has_lpg_connection: Optional[bool] = Field(None, example=False)
    is_houseless_or_kutcha_house: Optional[bool] = Field(None, example=True)
    is_secc_deprived: Optional[bool] = Field(None, example=True)
    is_traditional_artisan: Optional[bool] = Field(None, example=False)
    has_business_plan: Optional[bool] = Field(None, example=False)


class SchemeEligibilityResult(BaseModel):
    scheme_id: str
    scheme_name: str
    category: str
    ministry: str
    status: str  # eligible, potentially_eligible, ineligible
    verdict: str
    financial_assistance: str
    matched_criteria: List[str]
    failed_criteria: List[str]
    missing_info: List[str]
    official_url: str
    how_to_apply: str


class EligibilityResponse(BaseModel):
    total_evaluated: int
    results: List[SchemeEligibilityResult]
