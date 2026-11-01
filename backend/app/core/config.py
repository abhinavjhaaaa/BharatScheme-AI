from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BharatScheme AI"
    app_version: str = "1.0.0"
    debug: bool = True

    host: str = "127.0.0.1"
    port: int = 8000

    # Ollama settings (Local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b-instruct"

    # Embedding model
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Relevance threshold for RAG retrieval
    similarity_threshold: float = 0.35

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def project_root(self) -> Path:
        # backend/app/core/config.py -> parents[2] is project root
        return Path(__file__).resolve().parents[3]

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def schemes_file(self) -> Path:
        return self.data_dir / "schemes" / "schemes.json"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def default_faiss_index(self) -> Path:
        schemes_idx = self.processed_dir / "schemes_faiss.index"
        if schemes_idx.exists():
            return schemes_idx
        return self.processed_dir / "PM-KISAN_faiss.index"

    @property
    def default_faiss_metadata(self) -> Path:
        schemes_meta = self.processed_dir / "schemes_metadata.json"
        if schemes_meta.exists():
            return schemes_meta
        return self.processed_dir / "PM-KISAN_metadata.json"


settings = Settings()