import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.documents.chunker import chunk_text


sample_text = """
PM-KISAN is a Central Sector Scheme with 100% funding from the Government of India.

The scheme provides income support to eligible landholding farmer families.

Eligible farmer families receive financial assistance of Rs. 6000 per year.

The amount is transferred directly to the bank accounts of eligible beneficiaries.

Certain categories of beneficiaries are excluded from the scheme according to the operational guidelines.
"""


chunks = chunk_text(
    sample_text,
    chunk_size=200,
    chunk_overlap=50,
)


print(f"Total chunks: {len(chunks)}")

for index, chunk in enumerate(chunks, start=1):
    print(f"\n--- Chunk {index} ---")
    print(chunk)