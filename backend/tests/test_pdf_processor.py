import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.documents.pdf_processor import extract_pdf_pages


PDF_PATH = "data/raw/PM-KISAN/PM-KISAN-Operational-Guidelines.pdf"


pages = extract_pdf_pages(PDF_PATH)

print(f"Pages extracted: {len(pages)}")

if pages:
    print(f"\nFirst page number: {pages[0]['page_number']}")
    print("\nFirst page text:")
    print(pages[0]["text"][:1000])