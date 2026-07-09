"""
ChromaDB-backed vector store service.
"""

from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from core.config import settings


class VectorStoreService:
    """Vector database service for document chunks."""

    def __init__(self):
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory=settings.VECTOR_DB_PATH,
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
            )
        )
        self.embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE,
        )
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Document vector store"},
        )

    async def add_documents(
        self,
        doc_id: str,
        chunks: List,
        doc_name: Optional[str] = None,
    ) -> bool:
        """Add document chunks to the vector database."""
        try:
            normalized_chunks = [
                self._normalize_chunk(chunk, index)
                for index, chunk in enumerate(chunks)
            ]
            if not normalized_chunks:
                return True

            contents = [chunk["content"] for chunk in normalized_chunks]
            embeddings = self.embedding_model.encode(contents).tolist()
            ids = [
                f"{doc_id}_chunk_{chunk['chunk_index']}"
                for chunk in normalized_chunks
            ]
            metadatas = [
                self._build_metadata(doc_id, doc_name, chunk)
                for chunk in normalized_chunks
            ]

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
            )
            return True

        except Exception as exc:
            print(f"Failed to store document vectors: {exc}")
            raise exc

    async def search(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = None,
    ) -> List[dict]:
        """Search relevant document chunks."""
        if top_k is None:
            top_k = settings.TOP_K_RESULTS

        query_embedding = self.embedding_model.encode([query]).tolist()
        where = {"doc_id": {"$in": doc_ids}} if doc_ids else None

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where,
        )

        formatted_results = []
        if results["documents"] and len(results["documents"]) > 0:
            for index in range(len(results["documents"][0])):
                formatted_results.append(
                    {
                        "content": results["documents"][0][index],
                        "metadata": results["metadatas"][0][index],
                        "score": 1 - results["distances"][0][index],
                        "id": results["ids"][0][index],
                    }
                )

        return formatted_results

    async def delete_document(self, doc_id: str) -> bool:
        """Delete all vectors for a document."""
        try:
            results = self.collection.get(where={"doc_id": doc_id})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
            return True

        except Exception as exc:
            print(f"Failed to delete document vectors: {exc}")
            return False

    def _normalize_chunk(self, chunk, index: int) -> dict:
        if isinstance(chunk, dict):
            return {
                "content": chunk.get("content", ""),
                "section": chunk.get("section"),
                "chunk_index": chunk.get("chunk_index", index),
                "page": chunk.get("page"),
            }

        return {
            "content": str(chunk),
            "section": None,
            "chunk_index": index,
            "page": None,
        }

    def _build_metadata(
        self,
        doc_id: str,
        doc_name: Optional[str],
        chunk: dict,
    ) -> dict:
        metadata = {
            "doc_id": doc_id,
            "doc_name": doc_name or doc_id,
            "chunk_id": chunk["chunk_index"],
            "chunk_index": chunk["chunk_index"],
            "chunk_size": len(chunk["content"]),
        }
        if chunk.get("section") is not None:
            metadata["section"] = chunk["section"]
        if chunk.get("page") is not None:
            metadata["page"] = chunk["page"]
        return metadata
