"""Explicit, safe backend tools available to local agent skills."""

from typing import Optional

from core.config import settings
from services.note_service import NoteService
from services.output_service import OutputService
from services.retrieval_service import RetrievalService
from services.wiki_service import WikiService


TOOL_SCHEMAS = [
    {
        "name": "retrieve_sources",
        "description": "Retrieve ranked passages from selected local sources.",
        "parameters": {
            "question": "string",
            "doc_ids": "string[]",
            "top_k": "integer (optional)",
        },
    },
    {
        "name": "create_note",
        "description": "Persist a local note linked to selected source documents.",
        "parameters": {
            "title": "string",
            "content": "string",
            "doc_ids": "string[] (optional)",
            "conversation_id": "string (optional)",
        },
    },
    {
        "name": "create_output",
        "description": "Persist a generated markdown output with source provenance.",
        "parameters": {
            "kind": "string",
            "title": "string",
            "content": "string",
            "source_doc_ids": "string[]",
        },
    },
    {
        "name": "create_wiki_page",
        "description": "Persist a source-grounded local Wiki page.",
        "parameters": {
            "title": "string",
            "content": "string",
            "source_doc_ids": "string[]",
        },
    },
]


class ToolRegistry:
    """Allow skills to invoke only named, parameterized backend operations."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        note_service: Optional[NoteService] = None,
        output_service: Optional[OutputService] = None,
        wiki_service: Optional[WikiService] = None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.note_service = note_service or NoteService()
        self.output_service = output_service or OutputService()
        self.wiki_service = wiki_service or WikiService()
        self._handlers = {
            "retrieve_sources": self._retrieve_sources,
            "create_note": self._create_note,
            "create_output": self._create_output,
            "create_wiki_page": self._create_wiki_page,
        }

    def list_tools(self) -> list[dict]:
        """Return public schemas only; service configuration stays private."""
        return [
            {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": dict(schema["parameters"]),
            }
            for schema in TOOL_SCHEMAS
        ]

    async def run_tool(self, tool_name: str, params: dict) -> dict:
        """Run a registered tool and always return a structured result."""
        if not isinstance(tool_name, str):
            return {"ok": False, "error": "Tool name must be a string"}

        handler = self._handlers.get(tool_name)
        if handler is None:
            return {"ok": False, "error": "Unknown tool"}
        if not isinstance(params, dict):
            return {"ok": False, "error": "Tool parameters must be an object"}

        try:
            return {"ok": True, "result": await handler(params)}
        except (TypeError, ValueError):
            return {"ok": False, "error": "Tool parameters are invalid"}
        except Exception:
            return {"ok": False, "error": f"{tool_name} failed"}

    async def _retrieve_sources(self, params: dict) -> dict:
        question = self._required_string(params, "question")
        doc_ids = self._string_list(params.get("doc_ids", []), "doc_ids")
        top_k = params.get("top_k", settings.TOP_K_RESULTS)
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        sources = await self.retrieval_service.retrieve(
            question=question,
            doc_ids=doc_ids,
            top_k=top_k,
        )
        return {"sources": sources}

    async def _create_note(self, params: dict) -> dict:
        note_id = await self.note_service.create_note(
            title=self._required_string(params, "title"),
            content=self._required_string(params, "content"),
            doc_ids=self._string_list(params.get("doc_ids", []), "doc_ids"),
            conversation_id=self._optional_string(params.get("conversation_id"), "conversation_id"),
        )
        return {"note_id": note_id}

    async def _create_output(self, params: dict) -> dict:
        return self.output_service.create_output(
            kind=self._required_string(params, "kind"),
            title=self._required_string(params, "title"),
            content=self._required_string(params, "content"),
            source_doc_ids=self._string_list(
                params.get("source_doc_ids", []), "source_doc_ids"
            ),
        )

    async def _create_wiki_page(self, params: dict) -> dict:
        return self.wiki_service.create_page(
            title=self._required_string(params, "title"),
            content=self._required_string(params, "content"),
            source_doc_ids=self._string_list(
                params.get("source_doc_ids", []), "source_doc_ids"
            ),
        )

    @staticmethod
    def _required_string(params: dict, field: str) -> str:
        value = params.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        return value.strip()

    @staticmethod
    def _optional_string(value: object, field: str) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")
        return value

    @staticmethod
    def _string_list(value: object, field: str) -> list[str]:
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise ValueError(f"{field} must be a list of strings")
        return value
