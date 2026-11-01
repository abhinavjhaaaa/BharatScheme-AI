from typing import Optional
from fastapi import APIRouter, HTTPException
from backend.app.schemas.eligibility import EligibilityProfile, EligibilityResponse
from backend.app.services.eligibility.checker import EligibilityChecker

router = APIRouter(prefix="/api/eligibility", tags=["Eligibility"])

_checker: Optional[EligibilityChecker] = None


def get_checker() -> EligibilityChecker:
    global _checker
    if _checker is None:
        _checker = EligibilityChecker()
    return _checker


@router.post("", response_model=EligibilityResponse)
def evaluate_eligibility(profile: EligibilityProfile):
    """
    Evaluate user profile against government scheme criteria.
    Returns matched criteria, failed rules, and missing information.
    """
    try:
        checker = get_checker()
        profile_dict = profile.model_dump()
        scheme_id = profile_dict.pop("scheme_id", None)
        results = checker.check_eligibility(profile_dict, scheme_id=scheme_id)

        return {
            "total_evaluated": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating eligibility: {str(e)}"
        )
