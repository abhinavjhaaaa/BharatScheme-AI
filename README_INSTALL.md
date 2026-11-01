# BharatScheme AI — Update v1: 10 New Schemes + Hindi/Hinglish

## What is in this update (13 schemes total)

Original 3 (unchanged behaviour):
PM-KISAN, PM-USP-CSSS, AICTE-SWANATH-TECHNICAL

New 10 (user confirmed):
PM-JAY, PMAY-G, PMJDY, SSY, PMMY, APY, PM-VISHWAKARMA, PMJJBY, PMSBY, PMUY

## Files — copy each file to the matching path in your project

| This file | Copy to |
|---|---|
| data/schemes/schemes.json | data/schemes/schemes.json (replace, or merge: it already contains the original 3 + the 10 new) |
| backend/app/services/eligibility/checker.py | backend/app/services/eligibility/checker.py (replace) |
| backend/app/services/rag/rag_service.py | backend/app/services/rag/rag_service.py (replace) |
| backend/app/schemas/eligibility.py | backend/app/schemas/eligibility.py (replace) |
| frontend/index.html | frontend/index.html (replace) |
| frontend/js/app.js | frontend/js/app.js (replace) |

Do NOT copy anything else. Do NOT copy a venv folder.

## What changed and why

1. `checker.py` — The original 3 schemes keep their exact hand-written rules.
   All other schemes are now evaluated from their own `eligibility_criteria`
   in schemes.json (age range, income ceiling, gender, bank account, LPG,
   houseless/kutcha house, SECC list, artisan, business plan).
   This fixes the old generic fallback that said "General public citizen"
   and would have marked everyone Eligible for a new scheme.
   If a needed input is not supplied, the result is now
   "Potentially Eligible (Requires verification)", not Eligible.

2. `eligibility.py` (schema) — Adds 7 optional fields, all defaulting to
   None: gender, has_bank_account, has_lpg_connection,
   is_houseless_or_kutcha_house, is_secc_deprived, is_traditional_artisan,
   has_business_plan. None means "not supplied", so old requests still work.

3. `index.html` + `app.js` — New category chips (Health, Housing, Financial
   Inclusion, Savings, Business, Pension, Skill, Insurance, Energy),
   all 13 schemes in the chat filter and eligibility dropdown, a new
   "General Details" section in the eligibility form, and a Hinglish
   example prompt in chat. Category badges for new categories use the
   category name as a CSS class; if your style.css has no colour for
   e.g. `.health`, the badge still shows with the base badge style —
   colours are cosmetic only.

4. `rag_service.py` — Hindi/Hinglish auto-detection, no API change needed:
   - Devanagari script -> answer in Hindi (Devanagari).
   - Roman Hindi words (kya, kaise, kitna, mujhe, yojana, labh, aavedan...)
     -> answer in Hinglish (Roman script).
   - Otherwise -> English, as before.
   Hinglish words are translated to English ONLY for the FAISS search
   query, so English guideline chunks still match. The user's original
   question is kept for the LLM. Single-word queries for the new schemes
   (ayushman, awas, mudra, ujjwala, sukanya, atal, vishwakarma, bima,
   jandhan...) are expanded the same way the old schemes were.
   The hard-coded amounts list in the old system prompt was removed, so
   the LLM no longer leans on only the old 3 schemes' figures.
   `detected_language` is also returned in the chat result; your current
   ChatResponse model will simply ignore that extra field if it does
   not declare it.

## How to test (after copying)

```
# from the project root, with your venv activated
python -m py_compile backend/app/services/eligibility/checker.py backend/app/services/rag/rag_service.py backend/app/schemas/eligibility.py
uvicorn backend.main:app --reload
```

Then check:
- Explorer shows 13 schemes, and the new category chips filter them.
- Eligibility: APY, age 50 -> Not Eligible. APY, age 25 + bank account ->
  Eligible. PMUY, household already has LPG -> Not Eligible.
  PMUY, female + no LPG -> Eligible. A new scheme with age/bank left
  blank -> Potentially Eligible, not Eligible.
- Chat: "PM-JAY me kitna cover milta hai?" -> Hinglish answer.
  Hindi in Devanagari -> Hindi answer. English -> English answer.

## IMPORTANT — still to do for AI Chat on the new schemes

Explorer, Eligibility and Comparison work as soon as you copy the files
above. AI Chat will NOT yet answer about the 10 new schemes from
grounded documents, because your FAISS index was built from the old
guidelines only (51 vectors in your overview).

To finish chat for the new schemes:
1. Put each new scheme's official guideline PDF/text in
   data/raw/<SCHEME-ID>/ (for example data/raw/PM-JAY/).
2. Run your existing indexing script (the one that built
   data/processed/schemes_faiss.index + schemes_metadata.json).
3. Restart the backend and check /health shows healthy.

If your indexing script only indexes the original 3 schemes, send me
`backend/app/services/documents/index_all_schemes.py` (and pipeline.py)
and I will update it to index all 13. Do not skip this step and claim
chat is grounded for the new schemes — without their documents in the
index, the correct grounded behaviour is to decline, as before.

## Verification warning

The 10 new schemes' amounts, helplines and eligibility summaries in
schemes.json are drafted from public scheme knowledge and are marked
DRAFT in their source field. Verify each one against its official
guideline PDF before submission, especially amounts that change by
notification (for example Sukanya Samriddhi interest / deposit rules
and Mudra loan slabs). The original 3 schemes' data was not changed.
