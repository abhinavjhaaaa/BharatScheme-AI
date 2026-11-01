from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, example="How much financial assistance does PM-KISAN provide?")
    scheme_id: Optional[str] = Field(None, example="PM-KISAN")
    top_k: int = Field(5, ge=1, le=10)
    history: Optional[List[Dict[str, Any]]] = Field(default=None)


class SourceCitation(BaseModel):
    scheme_id: str
    source_file: str
    page_number: int
    chunk_id: str
    similarity_score: float
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    confidence: str = Field(..., example="high")
    is_grounded: bool = True
    detected_language: str = Field("en", example="en")
