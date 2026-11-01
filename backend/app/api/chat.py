from typing import Optional
from fastapi import APIRouter, HTTPException
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag.rag_service import RAGService

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


@router.post("", response_model=ChatResponse)
def chat_with_rag(request: ChatRequest):
    """
    RAG-powered conversational endpoint.
    Retrieves official document context from FAISS and generates
    grounded answers using local Ollama (Qwen2.5-3B-Instruct) with source citations.
    """
    try:
        service = get_rag_service()
        result = service.answer(
            question=request.question,
            top_k=request.top_k,
            scheme_id=request.scheme_id,
            history=request.history,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating RAG answer: {str(e)}"
        )
