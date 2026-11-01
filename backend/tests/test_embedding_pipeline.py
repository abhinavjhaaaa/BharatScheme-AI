import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.nlp.embedding_pipeline import create_embeddings


INPUT_PATH = "data/processed/PM-KISAN_chunks.jsonl"
OUTPUT_PATH = "data/processed/PM-KISAN_embeddings.jsonl"


create_embeddings(
    input_path=INPUT_PATH,
    output_path=OUTPUT_PATH,
)