import json
from pathlib import Path

from backend.app.services.nlp.embedding_service import EmbeddingService


def create_embeddings(
    input_path: str,
    output_path: str,
) -> None:
    """
    Generate embeddings for every chunk in a JSONL file.
    """

    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    chunks = []

    with input_file.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                chunks.append(json.loads(line))

    if not chunks:
        raise ValueError("No chunks found in input file.")

    texts = [chunk["text"] for chunk in chunks]

    service = EmbeddingService()

    embeddings = service.encode_texts(texts)

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Number of embeddings does not match number of chunks."
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open("w", encoding="utf-8") as file:
        for chunk, embedding in zip(chunks, embeddings):
            record = {
                **chunk,
                "embedding": embedding,
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"Processed chunks: {len(chunks)}")
    print(f"Embedding dimensions: {len(embeddings[0])}")
    print(f"Saved to: {output_path}")