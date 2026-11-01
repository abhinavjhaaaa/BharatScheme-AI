import json
from pathlib import Path

import numpy as np

from backend.app.services.nlp.embedding_service import EmbeddingService


class SemanticSearch:
    """
    Semantic search over embedded document chunks.
    """

    def __init__(self, embeddings_path: str):
        self.embeddings_path = Path(embeddings_path)

        if not self.embeddings_path.exists():
            raise FileNotFoundError(
                f"Embeddings file not found: {embeddings_path}"
            )

        self.chunks = self._load_embeddings()

        self.embedding_service = EmbeddingService()

        self.embedding_matrix = np.array(
            [chunk["embedding"] for chunk in self.chunks],
            dtype=np.float32,
        )

    def _load_embeddings(self) -> list[dict]:
        """
        Load embedded chunks from JSONL.
        """

        chunks = []

        with self.embeddings_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                if line.strip():
                    chunks.append(json.loads(line))

        if not chunks:
            raise ValueError("No embeddings found.")

        return chunks

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Find the most semantically similar chunks.
        """

        if not query.strip():
            return []

        query_embedding = self.embedding_service.encode_text(
            query
        )

        query_vector = np.array(
            query_embedding,
            dtype=np.float32,
        )

        scores = self.embedding_matrix @ query_vector

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []

        for index in top_indices:
            chunk = self.chunks[index].copy()

            chunk["similarity_score"] = float(
                scores[index]
            )

            # Embeddings are not needed in search results.
            chunk.pop("embedding", None)

            results.append(chunk)

        return results