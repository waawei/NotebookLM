"""
Chat data models
"""

from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    """Chat message"""
    role: str  # user or assistant
    content: str


class Citation(BaseModel):
    """Citation source"""
    number: int  # 引用编号 [1], [2], [3]...
    doc_id: str
    doc_name: str
    page: Optional[int]
    chunk_id: int
    content: str
    relevance_score: float


class ChatRequest(BaseModel):
    """Chat request"""
    question: str
    doc_ids: Optional[List[str]] = None
    conversation_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    """Chat response"""
    answer: str
    citations: List[Citation]
    conversation_id: str
