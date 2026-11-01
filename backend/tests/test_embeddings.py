import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.nlp.embedding_service import EmbeddingService


service = EmbeddingService()

text = "Eligible farmers receive financial assistance under PM-KISAN."

embedding = service.encode_text(text)

print(f"Embedding dimensions: {len(embedding)}")
print(f"First 10 values: {embedding[:10]}")