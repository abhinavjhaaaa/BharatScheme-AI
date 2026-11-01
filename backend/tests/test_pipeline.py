import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.documents.pipeline import process_pdf
from backend.app.services.documents.storage import save_chunks


PDF_PATH = "data/raw/PM-KISAN/PM-KISAN-Operational-Guidelines.pdf"
OUTPUT_PATH = "data/processed/PM-KISAN_chunks.jsonl"


chunks = process_pdf(
    pdf_path=PDF_PATH,
    scheme_id="PM-KISAN",
)

save_chunks(
    chunks=chunks,
    output_path=OUTPUT_PATH,
)


print(f"Total chunks created: {len(chunks)}")
print(f"Saved to: {OUTPUT_PATH}")

if chunks:
    print("\nFirst chunk:")
    print(chunks[0]["text"])

    print("\nMetadata:")
    print(f"Chunk ID: {chunks[0]['chunk_id']}")
    print(f"Page: {chunks[0]['page_number']}")
    print(f"Source: {chunks[0]['source_file']}")