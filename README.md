# BharatScheme AI — Smart Government Scheme Finder

**BharatScheme AI** is an intelligent, privacy-first, locally-hosted Indian government scheme intelligence system. It combines document processing, multilingual semantic embeddings, FAISS vector indexing, and local Large Language Models (Ollama `qwen2.5:3b-instruct`) with a FastAPI backend and a responsive frontend.

---

## 🏛️ Key Features

1. **Scheme Explorer & Search**
   - Search across verified Central and State government schemes by name, keyword, ministry, or category.
   - Filter by categories such as **Agriculture** and **Education & Scholarships**.
   - Rich modal dialog showing comprehensive scheme information: financial assistance amounts, benefits, detailed eligibility criteria, statutory exclusions, checklist of required documents, official portal links, and helpline contacts.

2. **Grounded AI Assistant (Local RAG)**
   - Answers questions strictly grounded in official government operational guidelines.
   - **Zero Hallucination Gating**: Questions with low retrieval similarity or unsupported domains are politely declined rather than hallucinated.
   - **Exact Citations**: Every factual answer returns the official source document, exact page number, similarity confidence percentage, and excerpt snippet.
   - Runs **100% locally and free** using Ollama (`qwen2.5:3b-instruct`). No paid API keys required.

3. **Deterministic Eligibility Evaluator**
   - Transparent rule-based assessment engine based on applicant's profile (occupation, annual family gross income, landholding status, student enrollment, Class 12 board percentile, technical degree enrollment, orphan/Covid/martyred category).
   - Generates an explainable breakdown of **Matched Requirements (✓)**, **Unmet Disqualifications (✕)**, and **Items Needing Verification**.

4. **Side-by-Side Scheme Comparison Matrix**
   - Compare 2 to 3 schemes simultaneously across financial assistance, target beneficiaries, income caps, key eligibility rules, required documents, and official portals.

---

## ⚙️ Architecture & RAG Pipeline

```
Official PDFs (data/raw/)
       │
       ▼
 [PyMuPDF Parser] (backend/app/services/documents/pdf_processor.py)
       │
       ▼
 [Text Cleaner & Chunker] (clean_text, chunk_text: 1000 chars, 200 overlap)
       │
       ▼
 [Multilingual Embeddings] (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
  *Cached singleton model optimized for 8 GB RAM*
       │
       ▼
 [FAISS Vector Index] (IndexFlatIP cosine similarity, 384 dimensions)
       │
       ▼
 [Grounded Prompt & Confidence Gating] (similarity_threshold: 0.35)
       │
       ▼
 [Local Ollama LLM] (qwen2.5:3b-instruct @ localhost:11434)
       │
       ▼
 [FastAPI Backend] ──► [Responsive Modern Frontend Dashboard]
```

---

## 💻 System Requirements & Optimization

- **Operating System**: Windows 10/11 (PowerShell)
- **Python**: 3.10.x
- **RAM**: Optimized for **8 GB RAM**:
  - Embedding model is loaded once via a shared singleton class in memory (~470 MB).
  - Uses 4-bit quantized Ollama `qwen2.5:3b-instruct` (~1.9 GB VRAM/RAM).
  - Clean Vanilla JS and CSS frontend without heavy Node.js or `node_modules` overhead.

---

## 🚀 Setup & Execution Guide (PowerShell)

### 1. Prerequisites
Ensure **Python 3.10** and **Ollama** are installed and Ollama has the Qwen2.5-3B model:

```powershell
# Verify Python
python --version

# Verify Ollama and pull the 3B model (if not already downloaded)
ollama list
ollama pull qwen2.5:3b-instruct
```

Make sure Ollama is running in the background (or launch `ollama serve` in a separate terminal).

### 2. Activate Virtual Environment & Install Dependencies

```powershell
# Navigate to project root
cd C:\Users\abhin\OneDrive\Desktop\BharatScheme-AI

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install / verify dependencies
pip install -r backend\requirements.txt
```

### 3. Run Automated Tests

Verify that all endpoints, FAISS vector search, and RAG grounding are operational:

```powershell
# Run the complete test suite
python backend\tests\test_api_endpoints.py

# Run standalone RAG retrieval test
python backend\tests\test_rag.py
```

### 4. Start the Application Server

Start the FastAPI application with live reloading:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Once started:
- **Interactive Web Interface**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
- **Interactive API Documentation (Swagger)**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- **Health Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

---

## 📡 API Reference

### 1. Health Check
`GET /health`
- **Response**:
  ```json
  {
    "status": "healthy",
    "app_name": "BharatScheme AI",
    "version": "1.0.0",
    "ollama_model": "qwen2.5:3b-instruct",
    "faiss_index_exists": true,
    "schemes_data_exists": true
  }
  ```

### 2. Scheme Search & Listing
`GET /api/schemes?category=Agriculture&q=farmer`
- Returns matching verified schemes with full eligibility rules, benefits, and portal links.

### 3. Grounded AI Chat (RAG)
`POST /api/chat`
- **Request**:
  ```json
  {
    "question": "How much financial assistance does PM-KISAN provide?",
    "top_k": 3
  }
  ```
- **Response**:
  ```json
  {
    "answer": "Under the PM-KISAN scheme, eligible farmers receive financial assistance of Rs. 6000 per year, paid in three equal installments of Rs. 2000 each every 4 months via Direct Benefit Transfer (DBT).",
    "sources": [
      {
        "scheme_id": "PM-KISAN",
        "source_file": "PM-KISAN-Operational-Guidelines.pdf",
        "page_number": 10,
        "chunk_id": "PM-KISAN-page-10-chunk-2",
        "similarity_score": 0.604,
        "snippet": "...financial benefit of Rs.6000/- per year is to be released to the eligible farmers in three installments of Rs.2000/- each..."
      }
    ],
    "confidence": "high",
    "is_grounded": true
  }
  ```

### 4. Deterministic Eligibility Checker
`POST /api/eligibility`
- **Request**:
  ```json
  {
    "occupation": "farmer",
    "annual_income": 180000,
    "is_landholding_farmer": true,
    "is_income_tax_payer": false,
    "is_institutional_landholder": false,
    "scheme_id": "PM-KISAN"
  }
  ```
- **Response**:
  ```json
  {
    "total_evaluated": 1,
    "results": [
      {
        "scheme_id": "PM-KISAN",
        "scheme_name": "Pradhan Mantri Kisan Samman Nidhi",
        "status": "eligible",
        "verdict": "Eligible",
        "financial_assistance": "Rs. 6,000 per year in 3 installments",
        "matched_criteria": [
          "Cultivable landholding farmer family",
          "Not an institutional landholder",
          "Not an income tax payer"
        ],
        "failed_criteria": [],
        "missing_info": []
      }
    ]
  }
  ```

### 5. Scheme Comparison
`POST /api/compare`
- **Request**:
  ```json
  {
    "scheme_ids": ["PM-KISAN", "PM-USP-CSSS"]
  }
  ```
- Returns side-by-side comparison across financial benefits, eligibility criteria, income caps, documents, and exclusions.

---

## 📁 Repository Structure

```
BharatScheme-AI/
├── .env                              # Environment configuration (Ollama, local settings)
├── .env.example                      # Template environment variables
├── README.md                         # Project documentation and guide
├── backend/
│   ├── main.py                       # FastAPI application entrypoint & static mounting
│   ├── requirements.txt              # Project dependencies (clean UTF-8)
│   ├── app/
│   │   ├── api/                      # API endpoint routers
│   │   │   ├── chat.py               # RAG chat endpoint (/api/chat)
│   │   │   ├── compare.py            # Comparison endpoint (/api/compare)
│   │   │   ├── eligibility.py        # Eligibility checker (/api/eligibility)
│   │   │   └── schemes.py            # Scheme search & details (/api/schemes)
│   │   ├── core/
│   │   │   └── config.py             # Typed Pydantic configuration & paths
│   │   ├── schemas/                  # Pydantic request & response models
│   │   │   ├── chat.py
│   │   │   ├── comparison.py
│   │   │   ├── eligibility.py
│   │   │   └── scheme.py
│   │   └── services/
│   │       ├── comparison/           # Scheme comparison engine
│   │       ├── documents/            # PDF processing, cleaning, chunking
│   │       ├── eligibility/          # Deterministic eligibility evaluator
│   │       ├── nlp/                  # Ollama LLM service, cached embeddings
│   │       ├── rag/                  # RAG service with threshold gating
│   │       └── retrieval/            # FAISS index and searcher
│   └── tests/                        # Automated unit & integration tests
├── data/
│   ├── processed/                    # Processed JSONL chunks, embeddings, FAISS indices
│   ├── raw/                          # Official government guideline PDFs and sources
│   └── schemes/
│       └── schemes.json              # Verified government scheme dataset
└── frontend/                         # Responsive Web Dashboard
    ├── index.html                    # Single-page application structure
    ├── css/
    │   └── style.css                 # Modern Indian-themed UI styling
    └── js/
    │   └── app.js                    # Reactive frontend application logic
```

---

## 🛡️ Data Grounding & Accuracy

- **Never Fabricated**: All factual statements are derived from official Ministry guidelines (Ministry of Agriculture, Ministry of Education, AICTE, and National Scholarship Portal).
- **Offline / Local**: Does not send user queries or document text to external third-party paid AI APIs.
