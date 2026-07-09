"""
Generated output service.
"""

import re
from typing import Optional

from services.document_metadata_store import DocumentMetadataStore
from services.llm_service import LLMService


SUPPORTED_OUTPUT_KINDS = {
    "summary": "Summary",
    "outline": "Outline",
    "review_cards": "Review Cards",
    "quiz": "Quiz",
    "paper_plan": "Paper Plan",
}


class OutputService:
    """Generate, persist, retrieve, and export source-grounded outputs."""

    def __init__(
        self,
        metadata_store: Optional[DocumentMetadataStore] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.metadata_store = metadata_store or DocumentMetadataStore()
        self.llm_service = llm_service or LLMService()

    async def generate_output(self, kind: str, source_doc_ids: list[str]) -> dict:
        self._validate_kind(kind)
        title = SUPPORTED_OUTPUT_KINDS[kind]
        prompt = self._build_prompt(kind, source_doc_ids)
        content = await self.llm_service.generate(prompt)
        return self.metadata_store.create_output(
            kind=kind,
            title=title,
            content=content.strip(),
            source_doc_ids=source_doc_ids,
        )

    def list_outputs(self, kind: Optional[str] = None) -> list[dict]:
        if kind:
            self._validate_kind(kind)
        return self.metadata_store.list_outputs(kind)

    def get_output(self, output_id: str) -> Optional[dict]:
        return self.metadata_store.get_output(output_id)

    def delete_output(self, output_id: str) -> bool:
        return self.metadata_store.delete_output(output_id)

    def export_output(self, output_id: str) -> Optional[dict]:
        output = self.get_output(output_id)
        if not output:
            return None

        filename = f"{self._filename_slug(output['title'])}.md"
        return {
            "filename": filename,
            "content_type": "text/markdown",
            "content": output["content"],
        }

    def _build_prompt(self, kind: str, source_doc_ids: list[str]) -> str:
        source_context = self._source_context(source_doc_ids)
        instructions = {
            "summary": "Write a concise markdown summary grounded only in the sources.",
            "outline": "Write a structured markdown outline with source-backed sections.",
            "review_cards": "Create review flashcards with question, answer, and source anchors.",
            "quiz": "Create a short quiz with answers and source anchors.",
            "paper_plan": "Create a paper plan with claims, evidence, counterpoints, and citation anchors.",
        }[kind]
        return f"""You are generating a reusable study artifact from local sources.

Instructions:
{instructions}

Requirements:
- Use markdown.
- Ground statements in the provided source metadata and summaries.
- Include source document IDs where useful.
- Do not invent facts beyond the source context.

Source context:
{source_context}

Generated artifact:"""

    def _source_context(self, source_doc_ids: list[str]) -> str:
        if not source_doc_ids:
            return "No source documents selected."

        parts = []
        for doc_id in source_doc_ids:
            document = self.metadata_store.get_document(doc_id)
            if not document:
                parts.append(f"- {doc_id}: missing document metadata")
                continue
            parts.append(
                "\n".join(
                    [
                        f"- Document ID: {document['doc_id']}",
                        f"  Title: {document['filename']}",
                        f"  Type: {document['file_type']}",
                        f"  Status: {document['status']}",
                        f"  Summary: {document.get('summary') or 'No summary available.'}",
                    ]
                )
            )
        return "\n".join(parts)

    def _validate_kind(self, kind: str) -> None:
        if kind not in SUPPORTED_OUTPUT_KINDS:
            raise ValueError(f"Unsupported output kind: {kind}")

    def _filename_slug(self, title: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
        return slug or "output"
