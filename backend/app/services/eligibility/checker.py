import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings


class EligibilityChecker:
    """
    Deterministic and explainable eligibility evaluation engine
    for registered government schemes.

    The three original schemes keep their exact, hand-written rules
    (PM-KISAN, PM-USP-CSSS, AICTE-SWANATH-TECHNICAL) so existing
    behaviour does not change.

    Every other scheme is evaluated from its own
    ``eligibility_criteria`` object in schemes.json, so adding a
    scheme to schemes.json no longer needs a new hard-coded branch
    here.  A criterion whose input is not supplied is reported as
    missing information (Potentially Eligible), never silently
    passed -- this replaces the old generic fallback that matched
    every new scheme as "General public citizen".
    """

    def __init__(self, schemes_file: Optional[Path] = None):
        self.schemes_file = schemes_file or settings.schemes_file
        self.schemes = self._load_schemes()

    def _load_schemes(self) -> List[Dict[str, Any]]:
        if not self.schemes_file.exists():
            return []
        with open(self.schemes_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def check_eligibility(
        self,
        profile: Dict[str, Any],
        scheme_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        schemes_to_check = (
            [s for s in self.schemes if s["scheme_id"] == scheme_id]
            if scheme_id
            else self.schemes
        )
        for scheme in schemes_to_check:
            results.append(self._evaluate_single_scheme(profile, scheme))
        return results

    # ------------------------------------------------------------------
    # Generic (data-driven) evaluation for all non-original schemes
    # ------------------------------------------------------------------
    def _evaluate_generic_scheme(
        self, profile: Dict[str, Any], scheme: Dict[str, Any]
    ) -> tuple[List[str], List[str], List[str]]:
        criteria = scheme.get("eligibility_criteria") or {}
        matched: List[str] = []
        failed: List[str] = []
        missing: List[str] = []

        income = profile.get("annual_income")
        age = profile.get("age")
        occupation = (profile.get("occupation") or "").lower()
        gender = (profile.get("gender") or "").lower()

        # --- Income ceiling -------------------------------------------------
        max_income = criteria.get("max_annual_income")
        if max_income is not None:
            if income is not None:
                if income <= max_income:
                    matched.append(
                        f"Family income \u20b9{income:,.0f} is within limit of "
                        f"\u20b9{max_income:,.0f}/yr"
                    )
                else:
                    failed.append(
                        f"Family income \u20b9{income:,.0f} exceeds max ceiling "
                        f"of \u20b9{max_income:,.0f}/yr"
                    )
            else:
                missing.append("Annual gross family income")

        # --- Age range -------------------------------------------------------
        min_age = criteria.get("min_age")
        max_age = criteria.get("max_age")
        if min_age is not None or max_age is not None:
            if age is not None:
                if min_age is not None and age < min_age:
                    failed.append(f"Age {age} is below minimum age of {min_age} years")
                elif max_age is not None and age > max_age:
                    failed.append(f"Age {age} is above maximum age of {max_age} years")
                else:
                    matched.append(f"Age {age} is within the eligible age range")
            else:
                missing.append("Age of applicant")

        # --- Gender -----------------------------------------------------------
        req_gender = (criteria.get("gender") or "").lower()
        if req_gender:
            if gender:
                if gender == req_gender:
                    matched.append(f"Scheme is for {req_gender} applicants")
                else:
                    failed.append(f"Scheme is for {req_gender} applicants")
            else:
                missing.append("Gender of applicant")

        # --- Occupation (only when the scheme names a specific one) ---------
        req_occ = (criteria.get("occupation") or "").lower()
        if req_occ and req_occ != "general":
            if occupation == req_occ:
                matched.append(f"Occupation matches: {req_occ}")
            elif occupation:
                # Do not hard-fail here: e.g. a salaried person may still
                # start a Mudra business. Report it for verification.
                missing.append(f"Confirmation of {req_occ} status / business plan")
            else:
                missing.append("Occupation / status")

        # --- Boolean profile flags -------------------------------------------
        # (flag, profile key, matched text, failed text, missing text)
        bool_checks = [
            (
                "requires_bank_account",
                "has_bank_account",
                "Has a savings bank / post office account",
                "A savings bank / post office account is required",
                "Bank account status",
            ),
            (
                "has_lpg_connection",
                "has_lpg_connection",
                # NOTE: this criterion means "must NOT have LPG" (PMUY).
                # It is handled specially below, not here.
                "",
                "",
                "",
            ),
            (
                "is_houseless_or_kutcha_house",
                "is_houseless_or_kutcha_house",
                "Houseless or living in a kutcha / dilapidated house",
                "Must be houseless or living in a kutcha / dilapidated house",
                "Housing status (houseless / kutcha house)",
            ),
            (
                "secc_deprived_household",
                "is_secc_deprived",
                "Household identified as deprived / vulnerable",
                "Household is not in the deprived / vulnerable list",
                "SECC / beneficiary-list status",
            ),
            (
                "is_traditional_artisan",
                "is_traditional_artisan",
                "Traditional artisan / craftsperson in a notified trade",
                "Must be a traditional artisan / craftsperson in a notified trade",
                "Artisan / trade status",
            ),
            (
                "requires_business_plan",
                "has_business_plan",
                "Has a viable business plan",
                "A viable business plan is required",
                "Business plan details",
            ),
        ]
        for crit_key, prof_key, ok_text, fail_text, miss_text in bool_checks:
            if not criteria.get(crit_key):
                continue
            if crit_key == "has_lpg_connection":
                continue  # handled below
            value = profile.get(prof_key)
            if value is True:
                matched.append(ok_text)
            elif value is False:
                failed.append(fail_text)
            else:
                missing.append(miss_text)

        # PMUY: the household must NOT already have an LPG connection.
        if criteria.get("has_lpg_connection") is False:
            value = profile.get("has_lpg_connection")
            if value is False:
                matched.append("Household does not already have an LPG connection")
            elif value is True:
                failed.append("Household already has an LPG connection")
            else:
                missing.append("Whether the household already has an LPG connection")

        # APY: income-tax payers cannot newly enrol from 1 Oct 2022.
        if scheme["scheme_id"] == "APY":
            if profile.get("is_income_tax_payer") is True:
                failed.append(
                    "Income-tax payers are not eligible to newly enrol in APY "
                    "from 1 October 2022"
                )
            elif profile.get("is_income_tax_payer") is False:
                matched.append("Not an income-tax payer")

        if not matched and not failed and not missing:
            missing.append("Scheme-specific profile details for verification")

        return matched, failed, missing

    # ------------------------------------------------------------------
    def _evaluate_single_scheme(
        self, profile: Dict[str, Any], scheme: Dict[str, Any]
    ) -> Dict[str, Any]:
        sid = scheme["scheme_id"]
        matched: List[str] = []
        failed: List[str] = []
        missing: List[str] = []

        income = profile.get("annual_income")
        occupation = (profile.get("occupation") or "").lower()
        is_farmer = profile.get("is_landholding_farmer")
        is_tax_payer = profile.get("is_income_tax_payer")
        is_inst_landholder = profile.get("is_institutional_landholder")
        is_student = profile.get("is_student")
        percentile_12 = profile.get("class_12_percentile")
        special_cat = (profile.get("special_category") or "none").lower()
        is_tech = profile.get("is_technical_degree_or_diploma")
        is_aicte = profile.get("is_aicte_approved_institution")

        if sid == "PM-KISAN":
            if is_farmer is True or occupation == "farmer":
                matched.append("Cultivable landholding farmer family")
            elif is_farmer is False:
                failed.append("Must own cultivable land (tenant/landless farmers excluded)")
            else:
                missing.append("Ownership of cultivable agricultural land")

            if is_inst_landholder is True:
                failed.append("Institutional landholders are legally excluded")
            elif is_inst_landholder is False:
                matched.append("Not an institutional landholder")

            if is_tax_payer is True:
                failed.append("Persons who paid income tax in last assessment year are excluded")
            elif is_tax_payer is False:
                matched.append("Not an income tax payer")
            else:
                missing.append("Confirmation of income tax status")

            if profile.get("is_constitutional_post_holder") is True:
                failed.append("Holders of constitutional posts are excluded")
            if profile.get("is_government_employee") is True:
                failed.append("Serving/retired government employees (non Group D) are excluded")

            benefit = scheme.get("financial_assistance", "Rs. 6,000 per year in 3 installments")

        elif sid == "PM-USP-CSSS":
            if is_student is True or occupation == "student":
                matched.append("Enrolled in higher education degree course")
            elif is_student is False:
                failed.append("Must be an enrolled regular college/university student")
            else:
                missing.append("Student enrollment confirmation")

            if income is not None:
                if income <= 450000:
                    matched.append(f"Family income \u20b9{income:,.0f} is within limit of \u20b94.5 Lakh/yr")
                else:
                    failed.append(f"Family income \u20b9{income:,.0f} exceeds max ceiling of \u20b94,50,000/yr")
            else:
                missing.append("Annual gross family income")

            if percentile_12 is not None:
                if percentile_12 >= 80.0:
                    matched.append(f"Class 12 board percentile ({percentile_12:.1f}%) meets >= 80th percentile requirement")
                else:
                    failed.append(f"Class 12 board percentile ({percentile_12:.1f}%) is below 80th percentile cutoff")
            else:
                missing.append("Class 12 board exam percentile / rank")

            if profile.get("is_regular_course") is False:
                failed.append("Correspondence/distance education courses are excluded")
            elif profile.get("is_regular_course") is True:
                matched.append("Pursuing regular full-time degree")

            benefit = scheme.get("financial_assistance", "Rs. 12,000/yr (UG) or Rs. 20,000/yr (PG)")

        elif sid == "AICTE-SWANATH-TECHNICAL":
            if is_tech is True or (is_student is True and "tech" in (profile.get("education_level") or "").lower()):
                matched.append("Pursuing Technical Degree or Diploma course")
            elif is_tech is False:
                failed.append("Must be enrolled in an approved Technical Degree/Diploma course")
            else:
                missing.append("Technical degree/diploma enrollment")

            if is_aicte is True:
                matched.append("Enrolled in AICTE-approved institution")
            elif is_aicte is False:
                failed.append("Institution must be AICTE approved")
            else:
                missing.append("AICTE approval status of institution")

            valid_cats = ["orphan", "covid_deceased_parents", "martyred_armed_forces_ward"]
            if special_cat in valid_cats:
                cat_label = {
                    "orphan": "Orphan student",
                    "covid_deceased_parents": "Both parents deceased due to COVID-19",
                    "martyred_armed_forces_ward": "Child of Armed/Paramilitary Forces martyred in action",
                }.get(special_cat, special_cat)
                matched.append(f"Qualifying category: {cat_label}")
            elif special_cat in ["none", ""]:
                failed.append("Must be an Orphan, Covid-19 affected child, or ward of martyred Armed Forces/CAPF personnel")
            else:
                failed.append(f"Category '{special_cat}' does not qualify for Swanath scheme")

            if income is not None:
                if income <= 800000:
                    matched.append(f"Family income \u20b9{income:,.0f} is within limit of \u20b98.0 Lakh/yr")
                else:
                    failed.append(f"Family income \u20b9{income:,.0f} exceeds max ceiling of \u20b98,00,000/yr")
            else:
                missing.append("Annual gross family income")

            benefit = scheme.get("financial_assistance", "Rs. 50,000 per annum")
        else:
            # New schemes: data-driven evaluation from schemes.json.
            matched, failed, missing = self._evaluate_generic_scheme(profile, scheme)
            benefit = scheme.get("financial_assistance", "N/A")

        if failed:
            status = "ineligible"
            verdict = "Not Eligible"
        elif missing:
            status = "potentially_eligible"
            verdict = "Potentially Eligible (Requires verification)"
        else:
            status = "eligible"
            verdict = "Eligible"

        return {
            "scheme_id": scheme["scheme_id"],
            "scheme_name": scheme["scheme_name"],
            "category": scheme.get("category", "General"),
            "ministry": scheme.get("ministry", ""),
            "status": status,
            "verdict": verdict,
            "financial_assistance": benefit,
            "matched_criteria": matched,
            "failed_criteria": failed,
            "missing_info": missing,
            "official_url": scheme.get("official_url", ""),
            "how_to_apply": scheme.get("how_to_apply", ""),
        }
