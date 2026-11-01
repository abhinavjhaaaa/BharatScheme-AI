import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["faiss_index_exists"] is True
    print("[PASS] /health passed")


def test_frontend_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "भारत" in response.text or "Scheme" in response.text
    assert "<!DOCTYPE html>" in response.text

    # Verify static flag asset is served
    flag_res = client.get("/static/assets/india_flag.png")
    assert flag_res.status_code == 200
    assert flag_res.headers["content-type"] == "image/png"
    print("[PASS] / (Frontend index.html & India flag image) served successfully")


def test_schemes_list():
    response = client.get("/api/schemes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert any(s["scheme_id"] == "PM-KISAN" for s in data["schemes"])
    print(f"[PASS] /api/schemes passed (Found {data['total']} schemes)")


def test_schemes_filter():
    response = client.get("/api/schemes?category=Agriculture")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(s["category"] == "Agriculture" for s in data["schemes"])
    print("[PASS] /api/schemes category filter passed")


def test_scheme_detail():
    response = client.get("/api/schemes/PM-KISAN")
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_id"] == "PM-KISAN"
    assert "financial_assistance" in data
    print("[PASS] /api/schemes/PM-KISAN detail passed")


def test_eligibility_farmer():
    payload = {
        "occupation": "farmer",
        "is_landholding_farmer": True,
        "is_income_tax_payer": False,
        "is_institutional_landholder": False,
        "scheme_id": "PM-KISAN",
    }
    response = client.post("/api/eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_evaluated"] == 1
    result = data["results"][0]
    assert result["status"] == "eligible"
    print("[PASS] /api/eligibility (farmer eligible) passed")


def test_eligibility_taxpayer_ineligible():
    payload = {
        "occupation": "farmer",
        "is_landholding_farmer": True,
        "is_income_tax_payer": True,
        "scheme_id": "PM-KISAN",
    }
    response = client.post("/api/eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()
    result = data["results"][0]
    assert result["status"] == "ineligible"
    assert any("tax" in r.lower() for r in result["failed_criteria"])
    print("[PASS] /api/eligibility (tax payer exclusion) passed")


def test_scheme_compare():
    payload = {
        "scheme_ids": ["PM-KISAN", "PM-USP-CSSS"]
    }
    response = client.post("/api/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_compared"] == 2
    assert len(data["comparison_matrix"]) > 0
    print("[PASS] /api/compare passed")


def test_chat_unsupported_rejection():
    # An entirely out-of-domain question should be declined without hallucination
    payload = {
        "question": "What is the recipe for chocolate chip cookies?",
        "top_k": 3,
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "low"
    assert data["is_grounded"] is False
    assert "could not find" in data["answer"].lower()
    print("[PASS] /api/chat anti-hallucination rejection passed")


def test_chat_grounded():
    payload = {
        "question": "How much financial assistance is provided under PM-KISAN and how is it paid?",
        "top_k": 3,
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_grounded"] is True
    assert len(data["sources"]) > 0
    assert any(term in data["answer"].lower() for term in ["6000", "6,000", "2000", "2,000", "installment", "instalment", "dbt", "pm-kisan"])
    print("[PASS] /api/chat grounded Q&A passed with citations")
    print(f"  Answer preview: {data['answer'][:120]}...")
    print(f"  Cited page: {data['sources'][0]['page_number']}")


def test_multilingual_scheme_search():
    # Search by Hindi term
    res_hi = client.get("/api/schemes?q=किसान")
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert any(s["scheme_id"] == "PM-KISAN" for s in data_hi["schemes"])

    # Search by Hinglish term
    res_hg = client.get("/api/schemes?q=chhatravritti")
    assert res_hg.status_code == 200
    data_hg = res_hg.json()
    assert any("scholarship" in s["scheme_name"].lower() or "csss" in s["scheme_id"].lower() for s in data_hg["schemes"])
    print("[PASS] Multilingual scheme search (Hindi & Hinglish) passed")


def test_chat_multilingual_and_history():
    # 1. Hindi query
    res_hi = client.post("/api/chat", json={"question": "पीएम किसान योजना में कितने पैसे मिलते हैं?", "top_k": 3})
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert data_hi["detected_language"] == "hi"
    assert data_hi["is_grounded"] is True
    assert len(data_hi["sources"]) > 0

    # 2. Hinglish query
    res_hg = client.post("/api/chat", json={"question": "PM kisan me kitna paisa milta hai?", "top_k": 3})
    assert res_hg.status_code == 200
    data_hg = res_hg.json()
    assert data_hg["detected_language"] == "hinglish"
    assert data_hg["is_grounded"] is True
    assert len(data_hg["sources"]) > 0

    # 3. Follow-up query with typo and history
    history = [
        {"role": "user", "content": "how much scholarships ?"},
        {"role": "assistant", "content": "Under PM-USP CSSS scholarship, students get Rs 12000 to Rs 20000"}
    ]
    res_typo = client.post("/api/chat", json={"question": "elegiblity", "top_k": 3, "history": history})
    assert res_typo.status_code == 200
    data_typo = res_typo.json()
    assert data_typo["is_grounded"] is True
    assert any("CSSS" in s["scheme_id"] or "SWANATH" in s["scheme_id"] for s in data_typo["sources"])
    print("[PASS] Multilingual chat (Hindi, Hinglish) and follow-up history resolution passed")


if __name__ == "__main__":
    test_health()
    test_frontend_root()
    test_schemes_list()
    test_schemes_filter()
    test_scheme_detail()
    test_eligibility_farmer()
    test_eligibility_taxpayer_ineligible()
    test_scheme_compare()
    test_chat_unsupported_rejection()
    test_chat_grounded()
    test_multilingual_scheme_search()
    test_chat_multilingual_and_history()
    print("\nALL API & RAG TESTS PASSED SUCCESSFULLY!")
