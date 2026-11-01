import json
from pathlib import Path


def save_chunks(chunks: list[dict], output_path: str) -> None:
    """
    Save processed chunks as JSONL.
    """

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(
                json.dumps(chunk, ensure_ascii=False)
                + "\n"
            )


def load_chunks(input_path: str) -> list[dict]:
    """
    Load chunks from a JSONL file.
    """

    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Chunk file not found: {input_path}"
        )

    chunks = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                chunks.append(json.loads(line))

    return chunks