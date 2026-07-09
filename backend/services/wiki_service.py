"""
Wiki page service.
"""

from typing import Optional

from services.document_metadata_store import DocumentMetadataStore
from services.llm_service import LLMService


class WikiService:
    """Create, edit, list, and generate source-grounded Wiki pages."""

    def __init__(
        self,
        metadata_store: Optional[DocumentMetadataStore] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.metadata_store = metadata_store or DocumentMetadataStore()
        self.llm_service = llm_service or LLMService()

    def create_page(
        self,
        title: str,
        content: str,
        source_doc_ids: list[str],
    ) -> dict:
        return self.metadata_store.create_wiki_page(title, content, source_doc_ids)

    def update_page(self, page_id: str, title: str, content: str) -> bool:
        return self.metadata_store.update_wiki_page(page_id, title, content)

    def get_page(self, page_id: str) -> Optional[dict]:
        return self.metadata_store.get_wiki_page(page_id)

    def list_pages(self) -> list[dict]:
        return self.metadata_store.list_wiki_pages()

    async def generate_page(self, title: str, source_doc_ids: list[str]) -> dict:
        prompt = self._build_prompt(title, source_doc_ids)
        content = (await self.llm_service.generate(prompt)).strip()
        return self.create_page(title, content, source_doc_ids)

    def export_page(self, page_id: str) -> Optional[dict]:
        page = self.get_page(page_id)
        if not page:
            return None
        return {
            "filename": f"{self._slug(page['title'])}.md",
            "content_type": "text/markdown",
            "content": self._markdown_export(
                title=page["title"],
                content=page["content"],
                source_doc_ids=page["source_doc_ids"],
            ),
        }

    def _build_prompt(self, title: str, source_doc_ids: list[str]) -> str:
        source_context = self._source_context(source_doc_ids)
        return f"""Create a source-grounded Wiki page in markdown.

Title: {title}

Requirements:
- Use only the local source context below.
- Start with a clear H1.
- Include concise sections and source document IDs as provenance.
- Do not invent unsupported facts.

Source context:
{source_context}

Wiki page:"""

    def _source_context(self, source_doc_ids: list[str]) -> str:
        if not source_doc_ids:
            return "No source documents selected."

        rows = []
        for doc_id in source_doc_ids:
            document = self.metadata_store.get_document(doc_id)
            if not document:
                rows.append(f"- {doc_id}: missing document metadata")
                continue
            rows.append(
                "\n".join(
                    [
                        f"- Document ID: {document['doc_id']}",
                        f"  Title: {document['filename']}",
                        f"  Summary: {document.get('summary') or 'No summary available.'}",
                    ]
                )
            )
        return "\n".join(rows)

    def _slug(self, title: str) -> str:
        return "".join(
            char.lower() if char.isalnum() else "-"
            for char in title
        ).strip("-") or "wiki-page"

    def _markdown_export(
        self,
        title: str,
        content: str,
        source_doc_ids: list[str],
    ) -> str:
        body = content.strip()
        if not body.startswith("#"):
            body = f"# {title}\n\n{body}"

        if not source_doc_ids:
            return body

        sources = "\n".join(f"- {doc_id}" for doc_id in source_doc_ids)
        return f"{body}\n\n---\n\n## Sources\n\n{sources}\n"
