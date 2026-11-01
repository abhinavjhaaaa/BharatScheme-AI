import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.retrieval.faiss_search import FAISSSearch


search_engine = FAISSSearch(
    index_path="data/processed/PM-KISAN_faiss.index",
    metadata_path="data/processed/PM-KISAN_metadata.json",
)


query = "How much financial assistance does a farmer receive?"

results = search_engine.search(
    query=query,
    top_k=3,
)

print("\n" + "=" * 80)
print(f"QUERY: {query}")
print("=" * 80)

for rank, result in enumerate(results, start=1):

    print(
        f"\n#{rank} "
        f"Score: {result['similarity_score']:.4f}"
    )

    print(f"Page: {result['page_number']}")
    print(f"Chunk: {result['chunk_id']}")

    print("\nText:")
    print(result["text"][:600])