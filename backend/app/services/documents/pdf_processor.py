from pathlib import Path

import pymupdf


def extract_pdf_pages(pdf_path: str) -> list[dict]:
    """
    Extract text from every page of a PDF.

    Returns a list containing:
    - page number
    - extracted text
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = []

    with pymupdf.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            if text:
                pages.append(
                    {
                        "page_number": page_number,
                        "text": text,
                    }
                )

    return pages