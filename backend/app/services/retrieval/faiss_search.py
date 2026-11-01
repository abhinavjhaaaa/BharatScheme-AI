import json
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from backend.app.services.nlp.embedding_service import EmbeddingService


class FAISSSearch:
    """
    Semantic search using a saved FAISS vector index and metadata file.
    """

    def __init__(
        self,
        index_path: str,
        metadata_path: str,
    ):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)

        if not self.index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {metadata_path}"
            )

        self.index = faiss.read_index(str(self.index_path))

        with self.metadata_path.open("r", encoding="utf-8") as file:
            self.metadata = json.load(file)

        self.embedding_service = EmbeddingService()

    def search(
        self,
        query: str,
        top_k: int = 5,
        scheme_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for top_k most similar chunks for a given query.
        Optionally filter by scheme_id.
        """
        if not query or not query.strip():
            return []

        query_embedding = self.embedding_service.encode_text(query.strip())
        query_vector = np.array([query_embedding], dtype=np.float32)

        # If filtering by scheme_id, retrieve a larger pool to filter down
        fetch_k = top_k * 4 if scheme_id else top_k
        fetch_k = min(fetch_k, self.index.ntotal)

        scores, indices = self.index.search(query_vector, fetch_k)

        results = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0 or index >= len(self.metadata):
                continue

            record = self.metadata[index].copy()

            if scheme_id and record.get("scheme_id") != scheme_id:
                continue

            record["similarity_score"] = round(float(score), 4)
            results.append(record)

            if len(results) >= top_k:
                break

        # Fallback: if scheme_id filter yielded 0 results, fall back to global top_k
        if scheme_id and not results:
            for score, index in zip(scores[0], indices[0]):
                if index < 0 or index >= len(self.metadata):
                    continue
                record = self.metadata[index].copy()
                record["similarity_score"] = round(float(score), 4)
                results.append(record)
                if len(results) >= top_k:
                    break

        return results