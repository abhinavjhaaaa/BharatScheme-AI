import os
from typing import Optional
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingService:
    """
    Generate semantic embeddings using a multilingual
    Sentence Transformer model.

    Optimized for 8 GB RAM by caching the underlying model
    as a shared class instance, with fast offline loading.
    """

    _cached_model: Optional[SentenceTransformer] = None
    _cached_model_name: Optional[str] = None

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        if (
            EmbeddingService._cached_model is None
            or EmbeddingService._cached_model_name != model_name
        ):
            try:
                # Fast offline load first to avoid network timeout retries
                EmbeddingService._cached_model = SentenceTransformer(
                    model_name,
                    local_files_only=True,
                )
            except Exception:
                EmbeddingService._cached_model = SentenceTransformer(model_name)
            EmbeddingService._cached_model_name = model_name

        self.model = EmbeddingService._cached_model

    def encode_text(self, text: str) -> list[float]:
        """
        Generate a normalized embedding vector for a single text.
        """
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def encode_texts(
        self,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
        """
        Generate normalized embeddings for multiple texts.
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()
