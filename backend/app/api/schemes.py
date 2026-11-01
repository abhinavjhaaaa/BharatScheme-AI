import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.core.config import settings
from backend.app.schemas.scheme import SchemeDetail, SchemeListResponse

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])

# Multilingual synonyms for scheme search
MULTILINGUAL_SYNONYMS = {
    "किसान": ["kisan", "farmer", "agriculture", "pm-kisan"],
    "खेती": ["kisan", "farmer", "agriculture"],
    "kheti": ["kisan", "farmer", "agriculture"],
    "छात्रवृत्ति": ["scholarship", "education", "student", "csss", "swanath"],
    "स्कॉलरशिप": ["scholarship", "education", "student"],
    "chhatravritti": ["scholarship", "education", "student"],
    "padhai": ["education", "scholarship", "student"],
    "पढ़ाई": ["education", "scholarship", "student"],
    "अनाथ": ["orphan", "swanath", "aicte"],
    "anarth": ["orphan", "swanath", "aicte"],
    "पैसा": ["financial", "assistance", "benefits", "pm-kisan"],
    "पैसे": ["financial", "assistance", "benefits", "pm-kisan"],
    "रुपये": ["financial", "assistance", "benefits"],
    "paisa": ["financial", "assistance", "benefits", "pm-kisan"],
    "paise": ["financial", "assistance", "benefits", "pm-kisan"],
    "योजना": ["scheme"],
    "yojana": ["scheme"],
    "yojna": ["scheme"],
}


def _load_schemes_data():
    if not settings.schemes_file.exists():
        return []
    with open(settings.schemes_file, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("", response_model=SchemeListResponse)
def list_schemes(
    q: Optional[str] = Query(None, description="Keyword search in English, Hindi, or Hinglish"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. Agriculture, Education)"),
    ministry: Optional[str] = Query(None, description="Filter by ministry"),
):
    """
    Search and filter registered government schemes with multilingual keyword support.
    """
    schemes = _load_schemes_data()

    if category:
        cat_lower = category.lower().strip()
        schemes = [s for s in schemes if s.get("category", "").lower() == cat_lower]

    if ministry:
        min_lower = ministry.lower().strip()
        schemes = [s for s in schemes if min_lower in s.get("ministry", "").lower()]

    if q:
        query = q.lower().strip()
        # Find any synonyms for the query word
        search_terms = {query}
        for kw, synonyms in MULTILINGUAL_SYNONYMS.items():
            if kw in query:
                search_terms.update(synonyms)

        filtered = []
        for s in schemes:
            name = s.get("scheme_name", "").lower()
            sid = s.get("scheme_id", "").lower()
            desc = s.get("description", "").lower()
            cat = s.get("category", "").lower()
            benefits = " ".join(s.get("benefits", [])).lower()
            elig_sum = s.get("eligibility_summary", "").lower()
            search_blob = f"{name} {sid} {desc} {cat} {benefits} {elig_sum}"

            if any(term in search_blob for term in search_terms):
                filtered.append(s)

        schemes = filtered

    return {
        "total": len(schemes),
        "schemes": schemes,
    }


@router.get("/{scheme_id}", response_model=SchemeDetail)
def get_scheme_by_id(scheme_id: str):
    """
    Get detailed verified information for a specific scheme.
    """
    schemes = _load_schemes_data()
    for s in schemes:
        if s.get("scheme_id", "").upper() == scheme_id.upper():
            return s

    raise HTTPException(
        status_code=404,
        detail=f"Scheme with ID '{scheme_id}' not found."
    )
