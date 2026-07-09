"""
Note data models.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class NoteLink(BaseModel):
    source_type: str
    source_id: str


class NoteCreate(BaseModel):
    title: str
    content: str
    doc_ids: Optional[List[str]] = []
    conversation_id: Optional[str] = None


class NoteFromMessageCreate(BaseModel):
    message_index: int
    conversation_id: str
    title: str
    content: str
    doc_ids: Optional[List[str]] = []


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_ids: Optional[List[str]] = None
    conversation_id: Optional[str] = None


class NoteResponse(BaseModel):
    note_id: str
    title: str
    content: str
    doc_ids: List[str]
    conversation_id: Optional[str] = None
    links: List[NoteLink] = []
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    notes: List[NoteResponse]
    total: int
