import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings


class SchemeComparator:
    """
    Service to compare multiple government schemes side-by-side.
    """

    def __init__(self, schemes_file: Optional[Path] = None):
        self.schemes_file = schemes_file or settings.schemes_file
        self.schemes = self._load_schemes()

    def _load_schemes(self) -> List[Dict[str, Any]]:
        if not self.schemes_file.exists():
            return []
        with open(self.schemes_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def compare_schemes(self, scheme_ids: List[str]) -> Dict[str, Any]:
        """
        Produce a structured side-by-side comparison for the requested scheme IDs.
        """
        selected = [s for s in self.schemes if s["scheme_id"] in scheme_ids]

        if not selected:
            return {
                "schemes": [],
                "comparison_matrix": {},
                "summary": "No matching schemes found for comparison.",
            }

        # Structure comparative attributes
        attributes = [
            ("Category", "category"),
            ("Ministry", "ministry"),
            ("Financial Assistance", "financial_assistance"),
            ("Target Beneficiaries", lambda s: s.get("eligibility_criteria", {}).get("target_group", "General")),
            ("Income Ceiling", lambda s: f"Up to ₹{s.get('eligibility_criteria', {}).get('max_annual_income'):,}/yr" if s.get('eligibility_criteria', {}).get('max_annual_income') else "No direct income ceiling (tax exclusion applies)"),
            ("Key Eligibility", "eligibility_summary"),
            ("Documents Required", lambda s: ", ".join(s.get("documents_required", [])[:4])),
            ("Official Portal", "official_url"),
            ("Helpline", "helpline"),
        ]

        matrix = []
        for label, getter in attributes:
            row = {"attribute": label, "values": {}}
            for s in selected:
                val = getter(s) if callable(getter) else s.get(getter, "N/A")
                row["values"][s["scheme_id"]] = val
            matrix.append(row)

        return {
            "scheme_ids": [s["scheme_id"] for s in selected],
            "schemes": selected,
            "comparison_matrix": matrix,
            "total_compared": len(selected),
        }
