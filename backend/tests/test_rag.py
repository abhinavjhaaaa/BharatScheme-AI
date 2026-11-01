import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.rag.rag_service import RAGService


INDEX_PATH = "data/processed/PM-KISAN_faiss.index"
METADATA_PATH = "data/processed/PM-KISAN_metadata.json"


def main():
    rag = RAGService(
        index_path=INDEX_PATH,
        metadata_path=METADATA_PATH,
    )

    question = "How much financial assistance does a farmer receive under PM-KISAN?"

    print("\nUser Question:")
    print(question)

    print("\nSearching documents and generating answer...\n")

    result = rag.answer(
        question=question,
        top_k=5,
    )

    print("========================================")
    print("ANSWER")
    print("========================================")
    print(result["answer"])

    print("\n========================================")
    print("SOURCES")
    print("========================================")

    for source in result["sources"]:
        print(
            f"- {source['source_file']} | "
            f"Page {source['page_number']} | "
            f"Similarity: {source['similarity_score']:.4f}"
        )


if __name__ == "__main__":
    main()