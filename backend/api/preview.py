"""
Safe typed preview API for Workbench Preview targets.
"""

import re
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from services.document_service import DocumentService
from services.note_service import NoteService
from services.output_service import OutputService
from services.wiki_service import WikiService

router = APIRouter()
document_service = DocumentService()
wiki_service = WikiService()
note_service = NoteService()
output_service = OutputService()

PREVIEW_LIMIT = 4000
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def _safe_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return _HTML_TAG_PATTERN.sub("", text)[:PREVIEW_LIMIT]


def _document_links(doc_ids: list[str]) -> List[Dict[str, str]]:
    return [{"type": "document", "id": doc_id, "title": doc_id} for doc_id in doc_ids]


def _as_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)


def _not_found(target_type: str) -> None:
    raise HTTPException(status_code=404, detail=f"{target_type} preview target not found")


@router.get("/{target_type}/{target_id}")
async def get_preview(target_type: str, target_id: str):
    if target_type == "document":
        document = document_service.metadata_store.get_document(target_id)
        if not document:
            _not_found(target_type)
        return {
            "type": "document",
            "id": document["doc_id"],
            "title": document["filename"],
            "content_preview": _safe_text(document.get("summary") or document.get("error_message") or ""),
            "metadata": {
                "file_type": document["file_type"],
                "status": document["status"],
                "total_chunks": document["total_chunks"],
                "summary_status": document.get("summary_status"),
            },
            "links": [],
        }

    if target_type == "wiki":
        page = wiki_service.get_page(target_id)
        if not page:
            _not_found(target_type)
        source_doc_ids = page.get("source_doc_ids", [])
        return {
            "type": "wiki",
            "id": page["page_id"],
            "title": page["title"],
            "content_preview": _safe_text(page.get("content", "")),
            "metadata": {
                "source_count": len(source_doc_ids),
                "updated_at": page.get("updated_at"),
            },
            "links": _document_links(source_doc_ids),
        }

    if target_type == "note":
        note = _as_dict(await note_service.get_note(target_id))
        if not note:
            _not_found(target_type)
        doc_ids = note.get("doc_ids", [])
        return {
            "type": "note",
            "id": note["note_id"],
            "title": note["title"],
            "content_preview": _safe_text(note.get("content", "")),
            "metadata": {
                "conversation_id": note.get("conversation_id"),
                "updated_at": note.get("updated_at"),
            },
            "links": _document_links(doc_ids),
        }

    if target_type == "output":
        output = output_service.get_output(target_id)
        if not output:
            _not_found(target_type)
        source_doc_ids = output.get("source_doc_ids", [])
        return {
            "type": "output",
            "id": output["output_id"],
            "title": output["title"],
            "content_preview": _safe_text(output.get("content", "")),
            "metadata": {
                "kind": output["kind"],
                "status": output.get("status", "active"),
                "source_count": len(source_doc_ids),
                "updated_at": output.get("updated_at"),
            },
            "links": _document_links(source_doc_ids),
        }

    raise HTTPException(status_code=400, detail="Unsupported preview target type")
