"""
RAG chat service with SQLite-backed conversation persistence.
"""

import uuid
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from core.config import settings
from models.chat import ChatMessage, ChatResponse, Citation
from services.document_metadata_store import DocumentMetadataStore
from services.llm_service import LLMService
from services.retrieval_service import RetrievalService
from services.vector_store import VectorStoreService


class ChatService:
    """Document question-answering service."""

    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        retrieval_service: Optional[RetrievalService] = None,
        metadata_store: Optional[DocumentMetadataStore] = None,
        llm_factory: Optional[Callable[[], LLMService]] = None,
    ):
        self.vector_store = vector_store
        self.retrieval_service = retrieval_service
        if self.retrieval_service is None:
            self.vector_store = self.vector_store or VectorStoreService()
            self.retrieval_service = RetrievalService(self.vector_store)
        self.llm_factory = llm_factory or LLMService
        self.metadata_store = metadata_store or DocumentMetadataStore()
        self.conversations = {}
        self._load_conversations()

    async def ask(
        self,
        question: str,
        doc_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        mode: str = "knowledge_base",
    ) -> ChatResponse:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        search_results = await self.retrieval_service.retrieve(
            question=question,
            doc_ids=doc_ids,
            top_k=settings.TOP_K_RESULTS,
        )

        if not search_results:
            return ChatResponse(
                answer="Sorry, I couldn't find relevant information in the documents.",
                citations=[],
                conversation_id=conversation_id,
            )

        context = self.retrieval_service.build_context(search_results)
        prompt = self._build_prompt(question, context, history, mode)
        answer = await self.llm_factory().generate(prompt)
        citations = self.retrieval_service.build_citations(search_results)
        self._save_conversation(conversation_id, question, answer, citations)

        return ChatResponse(
            answer=answer,
            citations=citations,
            conversation_id=conversation_id,
        )

    async def ask_stream(
        self,
        question: str,
        doc_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        mode: str = "knowledge_base",
    ):
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        yield {"type": "start", "conversation_id": conversation_id}

        search_results = await self.retrieval_service.retrieve(
            question=question,
            doc_ids=doc_ids,
            top_k=settings.TOP_K_RESULTS,
        )

        if not search_results:
            yield {
                "type": "content",
                "content": "Sorry, I couldn't find relevant information in the documents.",
            }
            yield {"type": "done"}
            return

        context = self.retrieval_service.build_context(search_results)
        prompt = self._build_prompt(question, context, history, mode)

        answer_chunks = []
        async for chunk in self.llm_factory().generate_stream(prompt):
            answer_chunks.append(chunk)
            yield {"type": "content", "content": chunk}

        full_answer = "".join(answer_chunks)
        citations = self.retrieval_service.build_citations(search_results)

        yield {"type": "citations", "citations": [c.dict() for c in citations]}
        self._save_conversation(conversation_id, question, full_answer, citations)
        yield {"type": "done", "conversation_id": conversation_id}

    def _load_conversations(self):
        """Load persisted conversations into the read-through cache."""
        try:
            self.conversations = {}
            for summary in self.metadata_store.list_conversations():
                conversation = self.metadata_store.get_conversation(
                    summary["conversation_id"]
                )
                if conversation:
                    self.conversations[summary["conversation_id"]] = (
                        self._store_to_api_conversation(conversation)
                    )
            print(f"Loaded {len(self.conversations)} conversations from SQLite")
        except Exception as exc:
            print(f"Failed to load conversations: {exc}")

    def _persist_conversation(self, conversation_id: str):
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return
        self.metadata_store.save_conversation(
            self._api_to_store_conversation(conversation)
        )

    def _build_prompt(
        self,
        question: str,
        context: str,
        history: Optional[List[ChatMessage]] = None,
        mode: str = "knowledge_base",
    ) -> str:
        prompt = """You are a professional document Q&A assistant. Please answer the user's question based on the following document content.

Requirements:
1. Only answer based on the provided document content, do not make up information
2. If there is no relevant information in the documents, clearly state so
3. Mark citation positions in the answer with [Source 1], [Source 2], etc.
4. The answer should be clear, accurate, and logical

"""

        prompt += self._mode_instructions(mode)
        prompt += "\n"

        if history:
            prompt += "\nConversation history:\n"
            for message in history[-3:]:
                prompt += f"{message.role}: {message.content}\n"

        prompt += f"\nRelevant document content:\n{context}\n"
        prompt += f"\nUser question: {question}\n"
        prompt += "\nPlease answer based on the above documents (remember to mark citation sources):\n"
        return prompt

    def _mode_instructions(self, mode: str) -> str:
        if mode == "review":
            return """Mode: Review
- Provide a study explanation that helps the user understand the material.
- Include review questions that check comprehension.
- Keep every claim grounded in the retrieved sources."""

        if mode == "paper":
            return """Mode: Paper
- Organize claims, evidence, counterpoints, and citation anchors.
- Separate source-backed claims from possible interpretation.
- Prefer phrasing that can be reused in paper notes or outlines."""

        return """Mode: Knowledge Base
- Provide direct source-grounded answers.
- Keep the response concise and operational.
- Cite the relevant source markers for factual claims."""

    def _save_conversation(
        self,
        conversation_id: str,
        question: str,
        answer: str,
        citations: List[Citation],
    ):
        now = datetime.now()
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "title": question[:80] or "Untitled conversation",
                "created_at": now,
                "updated_at": now,
                "messages": [],
            }

        self.conversations[conversation_id]["updated_at"] = now
        self.conversations[conversation_id]["messages"].append(
            {
                "question": question,
                "answer": answer,
                "citations": [citation.dict() for citation in citations],
                "timestamp": now,
            }
        )
        self._persist_conversation(conversation_id)

    async def get_conversation(self, conversation_id: str) -> Optional[dict]:
        conversation = self.conversations.get(conversation_id)
        if conversation:
            return conversation

        stored = self.metadata_store.get_conversation(conversation_id)
        if not stored:
            return None

        conversation = self._store_to_api_conversation(stored)
        self.conversations[conversation_id] = conversation
        return conversation

    async def list_conversations(self) -> List[dict]:
        return [
            {
                "id": conversation_id,
                "created_at": conversation["created_at"].isoformat(),
                "updated_at": conversation.get(
                    "updated_at", conversation["created_at"]
                ).isoformat(),
                "title": conversation.get("title", "Untitled conversation"),
                "message_count": len(conversation["messages"]),
                "last_message": (
                    conversation["messages"][-1]["question"]
                    if conversation["messages"]
                    else None
                ),
            }
            for conversation_id, conversation in self.conversations.items()
        ]

    async def delete_conversation(self, conversation_id: str) -> bool:
        self.conversations.pop(conversation_id, None)
        return self.metadata_store.delete_conversation(conversation_id)

    def _api_to_store_conversation(self, conversation: dict) -> dict:
        store_messages = []
        for index, message in enumerate(conversation.get("messages", [])):
            timestamp = self._ensure_datetime(message.get("timestamp"))
            store_messages.append(
                {
                    "message_id": f"{conversation['id']}-{index}-user",
                    "role": "user",
                    "content": message["question"],
                    "citations": [],
                    "created_at": timestamp,
                }
            )
            store_messages.append(
                {
                    "message_id": f"{conversation['id']}-{index}-assistant",
                    "role": "assistant",
                    "content": message["answer"],
                    "citations": message.get("citations", []),
                    "created_at": timestamp + timedelta(microseconds=1),
                }
            )

        return {
            "conversation_id": conversation["id"],
            "title": conversation.get("title", "Untitled conversation"),
            "created_at": conversation["created_at"],
            "updated_at": conversation.get("updated_at", conversation["created_at"]),
            "messages": store_messages,
        }

    def _store_to_api_conversation(self, conversation: dict) -> dict:
        messages = []
        pending_question = None

        for message in conversation.get("messages", []):
            created_at = self._ensure_datetime(message["created_at"])
            if message["role"] == "user":
                pending_question = {
                    "question": message["content"],
                    "timestamp": created_at,
                }
            elif message["role"] == "assistant":
                messages.append(
                    {
                        "question": (
                            pending_question["question"]
                            if pending_question
                            else ""
                        ),
                        "answer": message["content"],
                        "citations": message.get("citations", []),
                        "timestamp": (
                            pending_question["timestamp"]
                            if pending_question
                            else created_at
                        ),
                    }
                )
                pending_question = None

        return {
            "id": conversation["conversation_id"],
            "title": conversation.get("title", "Untitled conversation"),
            "created_at": self._ensure_datetime(conversation["created_at"]),
            "updated_at": self._ensure_datetime(conversation["updated_at"]),
            "messages": messages,
        }

    def _ensure_datetime(self, value) -> datetime:
        if isinstance(value, datetime):
            return value
        if value:
            return datetime.fromisoformat(str(value))
        return datetime.now()

    async def generate_suggested_questions(self, doc_ids: List[str]) -> List[str]:
        sample_chunks = []
        for doc_id in doc_ids[:3]:
            results = await self.vector_store.search(
                query="summary overview introduction",
                doc_ids=[doc_id],
                top_k=2,
            )
            sample_chunks.extend([result["content"] for result in results])

        if not sample_chunks:
            return [
                "What are the main topics covered in this document?",
                "Can you provide a summary of the key points?",
                "What are the most important findings?",
            ]

        context = "\n\n".join(sample_chunks[:3])
        prompt = f"""Based on the following document content, generate 5 questions that a user might want to ask about this document.

Requirements:
1. Questions should be specific and valuable
2. Cover the key themes of the document
3. Be clear and concise
4. Each question on a new line, starting with a number (1., 2., etc.)

Document content:
{context}

Generate 5 suggested questions:"""

        response = await self.llm_factory().generate(prompt)

        questions = []
        for line in response.strip().split("\n"):
            stripped = line.strip()
            if stripped and (stripped[0].isdigit() or stripped.startswith(("-", "*"))):
                question = stripped.lstrip("0123456789.-* ").strip()
                if question:
                    questions.append(question)

        return questions[:5]
