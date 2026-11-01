import json
from pathlib import Path

import faiss
import numpy as np


class FAISSIndex:
    """
    Build and search a FAISS vector index.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata = []

    def build(
        self,
        embeddings_path: str,
    ) -> None:
        """
        Build FAISS index from embedded JSONL chunks.
        """

        embeddings_file = Path(embeddings_path)

        if not embeddings_file.exists():
            raise FileNotFoundError(
                f"Embeddings file not found: {embeddings_path}"
            )

        vectors = []
        metadata = []

        with embeddings_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:
                if not line.strip():
                    continue

                record = json.loads(line)

                embedding = record.pop("embedding")

                vectors.append(embedding)
                metadata.append(record)

        if not vectors:
            raise ValueError("No embeddings found.")

        vector_matrix = np.array(
            vectors,
            dtype=np.float32,
        )

        if vector_matrix.shape[1] != self.dimension:
            raise ValueError(
                f"Expected dimension {self.dimension}, "
                f"got {vector_matrix.shape[1]}"
            )

        self.index.add(vector_matrix)
        self.metadata = metadata

        print(f"Vectors indexed: {self.index.ntotal}")
        print(f"Vector dimension: {self.dimension}")

    def save(
        self,
        index_path: str,
        metadata_path: str,
    ) -> None:
        """
        Save FAISS index and metadata.
        """

        index_file = Path(index_path)
        metadata_file = Path(metadata_path)

        index_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            str(index_file),
        )

        with metadata_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.metadata,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print(f"Index saved to: {index_path}")
        print(f"Metadata saved to: {metadata_path}")