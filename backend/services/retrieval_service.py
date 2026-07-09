"""
Retrieval, context assembly, and citation formatting for chat answers.
"""

from typing import List, Optional

from models.chat import Citation
from services.vector_store import VectorStoreService


class RetrievalService:
    """Focused boundary around vector retrieval and evidence formatting."""

    def __init__(self, vector_store: Optional[VectorStoreService] = None):
        self.vector_store = vector_store if vector_store is not None else VectorStoreService()

    async def retrieve(
        self,
        question: str,
        doc_ids: Optional[List[str]],
        top_k: int,
    ) -> List[dict]:
        return await self.vector_store.search(
            query=question,
            doc_ids=doc_ids,
            top_k=top_k,
        )

    def build_context(self, results: List[dict]) -> str:
        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            source_label = self._source_label(metadata)
            context_parts.append(
                "\n".join(
                    [
                        f"[Source {index}]",
                        result.get("content", ""),
                        source_label,
                    ]
                )
            )
        return "\n\n".join(context_parts)

    def build_citations(self, results: List[dict]) -> List[Citation]:
        citations = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            citations.append(
                Citation(
                    number=index,
                    doc_id=metadata.get("doc_id", ""),
                    doc_name=self._doc_name(metadata),
                    page=metadata.get("page"),
                    chunk_id=metadata.get("chunk_id", metadata.get("chunk_index", 0)),
                    content=result.get("content", ""),
                    relevance_score=result.get("score", 0.0),
                )
            )
        return citations

    def _source_label(self, metadata: dict) -> str:
        label_parts = [f"Document ID: {metadata.get('doc_id', 'unknown')}"]
        doc_name = metadata.get("doc_name")
        if doc_name:
            label_parts.append(f"Document: {doc_name}")
        if metadata.get("page") is not None:
            label_parts.append(f"Page: {metadata['page']}")
        if metadata.get("section"):
            label_parts.append(f"Section: {metadata['section']}")
        chunk_id = metadata.get("chunk_id", metadata.get("chunk_index"))
        if chunk_id is not None:
            label_parts.append(f"Chunk ID: {chunk_id}")
        return "(" + ", ".join(label_parts) + ")"

    def _doc_name(self, metadata: dict) -> str:
        if metadata.get("doc_name"):
            return metadata["doc_name"]
        doc_id = metadata.get("doc_id", "")
        return f"Document_{doc_id[:8]}" if doc_id else "Unknown document"
