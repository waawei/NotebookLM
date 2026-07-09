"""
笔记数据模型
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NoteCreate(BaseModel):
    """创建笔记请求"""
    title: str
    content: str
    doc_ids: Optional[List[str]] = []  # 关联的文档
    conversation_id: Optional[str] = None  # 关联的对话


class NoteUpdate(BaseModel):
    """更新笔记请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    doc_ids: Optional[List[str]] = None
    conversation_id: Optional[str] = None


class NoteResponse(BaseModel):
    """笔记响应"""
    note_id: str
    title: str
    content: str
    doc_ids: List[str]
    conversation_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    """笔记列表响应"""
    notes: List[NoteResponse]
    total: int
