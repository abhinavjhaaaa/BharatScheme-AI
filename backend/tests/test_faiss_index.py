import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.retrieval.faiss_index import FAISSIndex


EMBEDDINGS_PATH = "data/processed/PM-KISAN_embeddings.jsonl"
INDEX_PATH = "data/processed/PM-KISAN_faiss.index"
METADATA_PATH = "data/processed/PM-KISAN_metadata.json"


index = FAISSIndex(dimension=384)

index.build(
    embeddings_path=EMBEDDINGS_PATH
)

index.save(
    index_path=INDEX_PATH,
    metadata_path=METADATA_PATH,
)