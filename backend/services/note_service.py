"""
SQLite-backed note service.
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

from core.config import settings
from models.note import NoteResponse
from services.document_metadata_store import DocumentMetadataStore


class NoteService:
    """Manage notes and their links to local sources."""

    def __init__(self, metadata_store: Optional[DocumentMetadataStore] = None):
        self.metadata_store = metadata_store or DocumentMetadataStore()
        self.notes_dir = os.path.join(settings.UPLOAD_DIR, "notes")
        self._migrate_json_notes()

    async def create_note(
        self,
        title: str,
        content: str,
        doc_ids: List[str] = None,
        conversation_id: str = None,
    ) -> str:
        note_id = str(uuid.uuid4())
        now = datetime.now()
        note = {
            "note_id": note_id,
            "title": title,
            "content": content,
            "doc_ids": doc_ids or [],
            "conversation_id": conversation_id,
            "created_at": now,
            "updated_at": now,
        }
        self.metadata_store.save_note(note)
        self._save_standard_links(note_id, note["doc_ids"], conversation_id)
        return note_id

    async def create_note_from_message(
        self,
        message_index: int,
        conversation_id: str,
        title: str,
        content: str,
        doc_ids: List[str] = None,
    ) -> str:
        note_id = await self.create_note(
            title=title,
            content=content,
            doc_ids=doc_ids or [],
            conversation_id=conversation_id,
        )
        self.metadata_store.save_note_link(note_id, "message", f"{conversation_id}:{message_index}")
        return note_id

    async def get_note(self, note_id: str) -> Optional[NoteResponse]:
        note = self.metadata_store.get_note(note_id)
        if not note:
            return None
        return NoteResponse(**note)

    async def list_notes(self) -> List[NoteResponse]:
        return [
            NoteResponse(**note)
            for note in self.metadata_store.list_notes()
        ]

    async def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        doc_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
    ) -> bool:
        current = self.metadata_store.get_note(note_id)
        if not current:
            return False

        updated = {
            **current,
            "title": current["title"] if title is None else title,
            "content": current["content"] if content is None else content,
            "doc_ids": current["doc_ids"] if doc_ids is None else doc_ids,
            "conversation_id": current["conversation_id"] if conversation_id is None else conversation_id,
            "updated_at": datetime.now(),
        }
        self.metadata_store.save_note(updated)
        self._save_standard_links(note_id, updated["doc_ids"], updated["conversation_id"])
        return True

    async def delete_note(self, note_id: str) -> bool:
        return self.metadata_store.delete_note(note_id)

    def _save_standard_links(
        self,
        note_id: str,
        doc_ids: List[str],
        conversation_id: Optional[str],
    ) -> None:
        if conversation_id:
            self.metadata_store.save_note_link(note_id, "conversation", conversation_id)
        for doc_id in doc_ids or []:
            self.metadata_store.save_note_link(note_id, "document", doc_id)

    def _migrate_json_notes(self) -> None:
        if self.metadata_store.list_notes() or not os.path.isdir(self.notes_dir):
            return

        for filename in os.listdir(self.notes_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.notes_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    note = json.load(file)
                note["created_at"] = datetime.fromisoformat(note["created_at"])
                note["updated_at"] = datetime.fromisoformat(note["updated_at"])
                note.setdefault("doc_ids", [])
                note.setdefault("conversation_id", None)
                self.metadata_store.save_note(note)
                self._save_standard_links(
                    note["note_id"],
                    note["doc_ids"],
                    note.get("conversation_id"),
                )
            except Exception as exc:
                print(f"Failed to migrate note {filename}: {exc}")
