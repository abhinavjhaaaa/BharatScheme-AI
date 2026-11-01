import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import faiss
import numpy as np

from backend.app.core.config import settings
from backend.app.services.documents.chunker import chunk_text
from backend.app.services.documents.text_cleaner import clean_text
from backend.app.services.nlp.embedding_service import EmbeddingService


def build_all_schemes_index():
    raw_dir = settings.data_dir / "raw"
    processed_dir = settings.processed_dir
    schemes_file = settings.schemes_file

    all_chunks = []

    # 1. Existing PM-KISAN chunks
    pmkisan_chunks_file = processed_dir / "PM-KISAN_chunks.jsonl"
    if pmkisan_chunks_file.exists():
        with open(pmkisan_chunks_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunk = json.loads(line)
                    chunk["text"] = clean_text(chunk["text"])
                    all_chunks.append(chunk)
        print(f"Loaded {len(all_chunks)} PM-KISAN chunks from existing dataset.")

    # 2. PM-USP-CSSS guidelines
    csss_file = raw_dir / "PM-USP-CSSS" / "PM-USP-CSSS-Guidelines.txt"
    if csss_file.exists():
        text = csss_file.read_text(encoding="utf-8")
        cleaned = clean_text(text)
        # Split by sections or chunks
        chunks = chunk_text(cleaned, chunk_size=900, chunk_overlap=180)
        for idx, ch in enumerate(chunks, start=1):
            all_chunks.append({
                "chunk_id": f"PM-USP-CSSS-sec-{idx}",
                "scheme_id": "PM-USP-CSSS",
                "page_number": idx,
                "chunk_index": idx,
                "text": ch,
                "source_file": "PM-USP-CSSS-Guidelines.txt"
            })
        print(f"Added {len(chunks)} chunks for PM-USP-CSSS.")

    # 3. AICTE-SWANATH guidelines
    swanath_file = raw_dir / "AICTE-SWANATH-TECHNICAL" / "AICTE-SWANATH-Guidelines.txt"
    if swanath_file.exists():
        text = swanath_file.read_text(encoding="utf-8")
        cleaned = clean_text(text)
        chunks = chunk_text(cleaned, chunk_size=900, chunk_overlap=180)
        for idx, ch in enumerate(chunks, start=1):
            all_chunks.append({
                "chunk_id": f"AICTE-SWANATH-sec-{idx}",
                "scheme_id": "AICTE-SWANATH-TECHNICAL",
                "page_number": idx,
                "chunk_index": idx,
                "text": ch,
                "source_file": "AICTE-SWANATH-Guidelines.txt"
            })
        print(f"Added {len(chunks)} chunks for AICTE-SWANATH-TECHNICAL.")

    # 4. Summary & benefits chunks from schemes.json
    if schemes_file.exists():
        with open(schemes_file, "r", encoding="utf-8") as f:
            schemes = json.load(f)
        for s in schemes:
            sid = s["scheme_id"]
            summary_text = (
                f"Scheme Name: {s['scheme_name']}\n"
                f"Category: {s['category']} | Ministry: {s['ministry']}\n"
                f"Financial Assistance / Scholarship Amount: {s.get('financial_assistance', '')}\n"
                f"Key Benefits:\n- " + "\n- ".join(s.get("benefits", [])) + "\n"
                f"Eligibility Criteria Summary: {s.get('eligibility_summary', '')}\n"
                f"Exclusions:\n- " + "\n- ".join(s.get("exclusions", [])) + "\n"
                f"Documents Required:\n- " + "\n- ".join(s.get("documents_required", [])) + "\n"
                f"How to Apply: {s.get('how_to_apply', '')}"
            )
            all_chunks.append({
                "chunk_id": f"{sid}-verified-summary",
                "scheme_id": sid,
                "page_number": 1,
                "chunk_index": 1,
                "text": summary_text,
                "source_file": f"{sid}-Official-Portal.json"
            })
        print(f"Added {len(schemes)} verified summary chunks from schemes.json.")

    print(f"\nTotal combined chunks across all schemes: {len(all_chunks)}")

    # 5. Embed all chunks
    embedder = EmbeddingService()
    texts = [c["text"] for c in all_chunks]
    embeddings = embedder.encode_texts(texts)

    # 6. Save combined JSONL chunks and embeddings
    chunks_out = processed_dir / "schemes_chunks.jsonl"
    with open(chunks_out, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    embeddings_out = processed_dir / "schemes_embeddings.jsonl"
    with open(embeddings_out, "w", encoding="utf-8") as f:
        for c, emb in zip(all_chunks, embeddings):
            record = {**c, "embedding": emb}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 7. Build and save FAISS index
    vector_matrix = np.array(embeddings, dtype=np.float32)
    index = faiss.IndexFlatIP(vector_matrix.shape[1])
    index.add(vector_matrix)

    index_out = processed_dir / "schemes_faiss.index"
    metadata_out = processed_dir / "schemes_metadata.json"

    faiss.write_index(index, str(index_out))
    with open(metadata_out, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nSuccessfully built combined multi-scheme index with {index.ntotal} vectors!")
    print(f"Index saved to: {index_out}")
    print(f"Metadata saved to: {metadata_out}")


if __name__ == "__main__":
    build_all_schemes_index()
