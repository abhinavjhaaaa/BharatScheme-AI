from typing import Optional
from fastapi import APIRouter, HTTPException
from backend.app.schemas.comparison import CompareRequest, CompareResponse
from backend.app.services.comparison.comparator import SchemeComparator

router = APIRouter(prefix="/api/compare", tags=["Scheme Comparison"])

_comparator: Optional[SchemeComparator] = None


def get_comparator() -> SchemeComparator:
    global _comparator
    if _comparator is None:
        _comparator = SchemeComparator()
    return _comparator


@router.post("", response_model=CompareResponse)
def compare_schemes(request: CompareRequest):
    """
    Compare 2 or more schemes side-by-side across key attributes.
    """
    try:
        comparator = get_comparator()
        result = comparator.compare_schemes(request.scheme_ids)
        if not result["schemes"]:
            raise HTTPException(
                status_code=404,
                detail="None of the specified scheme IDs were found."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing schemes: {str(e)}"
        )
