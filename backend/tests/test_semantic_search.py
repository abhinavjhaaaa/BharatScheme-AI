import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.retrieval.semantic_search import SemanticSearch


EMBEDDINGS_PATH = "data/processed/PM-KISAN_embeddings.jsonl"


search_engine = SemanticSearch(EMBEDDINGS_PATH)


queries = [
    "How much financial assistance does the farmer receive?",
    "Who is eligible for PM-KISAN?",
    "What is the objective of this scheme?",
]


for query in queries:
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    results = search_engine.search(
        query=query,
        top_k=3,
    )

    for rank, result in enumerate(results, start=1):
        print(
            f"\n#{rank} "
            f"Score: {result['similarity_score']:.4f}"
        )

        print(
            f"Page: {result['page_number']}"
        )

        print(
            f"Chunk: {result['chunk_id']}"
        )

        print(
            result["text"][:500]
        )