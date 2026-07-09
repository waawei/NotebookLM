"""
数据模型定义
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentMetadata(BaseModel):
    """文档元数据"""
    doc_id: str
    filename: str
    file_type: str
    file_size: int
    upload_time: datetime
    status: str  # pending, processing, completed, failed
    total_chunks: int = 0
    summary: Optional[str] = None  # 文档摘要
    error_message: Optional[str] = None


class DocumentResponse(BaseModel):
    """文档响应"""
    doc_id: str
    filename: str
    file_type: str
    upload_time: datetime
    status: str
    total_chunks: int
    summary: Optional[str] = None  # 文档摘要
    page_count: Optional[int] = None


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentResponse]
    total: int


class DocumentChunk(BaseModel):
    """文档分块"""
    chunk_id: int
    doc_id: str
    content: str
    metadata: dict


class ChunkWithScore(BaseModel):
    """带相似度分数的文档块"""
    chunk: DocumentChunk
    score: float
