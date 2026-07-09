"""
Retrieval, context assembly, and citation formatting for chat answers.
"""

import re
from typing import List, Optional

from core.config import settings
from models.chat import Citation
from services.vector_store import VectorStoreService


class RetrievalService:
    """Focused boundary around vector retrieval and evidence formatting."""

    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        llm_service=None,
    ):
        self.vector_store = vector_store if vector_store is not None else VectorStoreService()
        self.llm_service = llm_service

    async def retrieve(
        self,
        question: str,
        doc_ids: Optional[List[str]],
        top_k: int,
        history: Optional[List[dict]] = None,
    ) -> List[dict]:
        rewritten_question = await self._rewrite_query_if_enabled(
            question,
            history or [],
        )
        results = await self.vector_store.search(
            query=rewritten_question,
            doc_ids=doc_ids,
            top_k=top_k,
        )
        return self.rerank(question, results)

    def rewrite_query(self, question: str, history: List[dict]) -> str:
        if not settings.ENABLE_QUERY_REWRITE:
            return question
        if not history:
            return question
        history_text = " ".join(
            item.get("content", "")
            for item in history[-4:]
            if isinstance(item, dict)
        ).strip()
        return f"{history_text}\n{question}" if history_text else question

    def rerank(self, question: str, results: List[dict]) -> List[dict]:
        if not results:
            return []

        return sorted(
            results,
            key=lambda result: self._ranking_score(question, result),
            reverse=True,
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
                    section=metadata.get("section"),
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

    async def _rewrite_query_if_enabled(
        self,
        question: str,
        history: List[dict],
    ) -> str:
        if not settings.ENABLE_QUERY_REWRITE:
            return question

        try:
            if self.llm_service is None:
                from services.llm_service import LLMService

                self.llm_service = LLMService()

            history_text = "\n".join(
                f"{item.get('role', 'user')}: {item.get('content', '')}"
                for item in history[-4:]
                if isinstance(item, dict)
            )
            prompt = f"""Rewrite the user question into one concise retrieval query.

Conversation history:
{history_text}

Question:
{question}

Retrieval query:"""
            rewritten = (await self.llm_service.generate(prompt)).strip()
            return rewritten or question
        except Exception:
            return question

    def _ranking_score(self, question: str, result: dict) -> float:
        metadata = result.get("metadata") or {}
        score = float(result.get("score", 0.0))
        question_terms = self._terms(question)

        doc_name = metadata.get("doc_name", "")
        section = metadata.get("section", "")
        content = result.get("content", "")

        title_terms = self._terms(doc_name)
        section_terms = self._terms(section)
        content_terms = self._terms(content)

        if title_terms:
            score += 0.15 * len(question_terms.intersection(title_terms))
        if section_terms:
            score += 0.2 * len(question_terms.intersection(section_terms))
        normalized_question = self._normalize_text(question)
        normalized_section = self._normalize_text(section)
        if normalized_section and normalized_section in normalized_question:
            score += 0.5
        score += 0.05 * len(question_terms.intersection(content_terms))
        return score

    def _terms(self, text: str) -> set[str]:
        return {
            term
            for term in re.findall(r"[a-z0-9]+", text.lower())
            if len(term) > 2
        }

    def _normalize_text(self, text: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", text.lower()))
