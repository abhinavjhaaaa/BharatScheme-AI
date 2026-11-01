from pathlib import Path

from backend.app.services.documents.pdf_processor import extract_pdf_pages
from backend.app.services.documents.text_cleaner import clean_text
from backend.app.services.documents.chunker import chunk_text


def process_pdf(
    pdf_path: str,
    scheme_id: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """
    Process a PDF into clean, searchable chunks.

    Each chunk contains:
    - scheme_id
    - page_number
    - chunk_id
    - text
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = extract_pdf_pages(pdf_path)

    processed_chunks = []

    for page in pages:
        cleaned_text = clean_text(page["text"])

        chunks = chunk_text(
            cleaned_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for chunk_index, chunk in enumerate(chunks, start=1):
            processed_chunks.append(
                {
                    "chunk_id": (
                        f"{scheme_id}-"
                        f"page-{page['page_number']}-"
                        f"chunk-{chunk_index}"
                    ),
                    "scheme_id": scheme_id,
                    "page_number": page["page_number"],
                    "chunk_index": chunk_index,
                    "text": chunk,
                    "source_file": path.name,
                }
            )

    return processed_chunks