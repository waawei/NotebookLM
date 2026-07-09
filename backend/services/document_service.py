"""
Document service for upload, parsing, vectorization, and metadata persistence.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile

from core.config import settings
from models.document import DocumentMetadata, DocumentResponse
from services.document_metadata_store import DocumentMetadataStore
from services.document_parser import DocumentParser
from services.llm_service import LLMService
from services.vector_store import VectorStoreService


class DocumentService:
    """Document management service."""

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.parser = DocumentParser()
        self.vector_store = VectorStoreService()
        self.llm_service = LLMService()
        self.metadata_store = DocumentMetadataStore()
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_document(self, file: UploadFile) -> str:
        """Save an uploaded file and create pending metadata."""
        doc_id = str(uuid.uuid4())
        filename = file.filename or "upload"
        file_path = os.path.join(self.upload_dir, f"{doc_id}_{filename}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=filename,
            file_type=filename.split(".")[-1].lower(),
            file_size=len(content),
            upload_time=datetime.now(),
            status="pending",
        )

        self.metadata_store.upsert_document(
            metadata=metadata,
            source_path=file_path,
            source_type="file",
        )
        return doc_id

    async def upload_url(self, url: str) -> str:
        """Create pending metadata for a URL source."""
        doc_id = str(uuid.uuid4())
        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=url,
            file_type="url",
            file_size=0,
            upload_time=datetime.now(),
            status="pending",
        )

        self.metadata_store.upsert_document(
            metadata=metadata,
            source_url=url,
            source_type="url",
        )
        return doc_id

    async def process_url(self, doc_id: str) -> bool:
        """Fetch, chunk, vectorize, and summarize a URL source."""
        try:
            record = self.metadata_store.get_document(doc_id)
            if not record:
                raise ValueError(f"Document {doc_id} does not exist")

            self.metadata_store.update_status(doc_id, "processing")
            url = record["source_url"]
            text = self.parser.parse_url(url)
            chunks = self.parser.chunk_text(text)
            await self.vector_store.add_documents(doc_id, chunks)
            summary = await self._generate_summary(text)

            self.metadata_store.update_status(
                doc_id=doc_id,
                status="completed",
                total_chunks=len(chunks),
                summary=summary,
                error_message=None,
            )
            return True

        except Exception as e:
            self.metadata_store.update_status(doc_id, "failed", error_message=str(e))
            raise e

    async def process_document(self, doc_id: str) -> bool:
        """Parse, chunk, vectorize, and summarize an uploaded document."""
        try:
            record = self.metadata_store.get_document(doc_id)
            if not record:
                raise ValueError(f"Document {doc_id} does not exist")

            self.metadata_store.update_status(doc_id, "processing")
            file_path = record["source_path"]
            text = self.parser.parse_file(file_path)
            chunks = self.parser.chunk_text(text)
            await self.vector_store.add_documents(doc_id, chunks)
            summary = await self._generate_summary(text)

            self.metadata_store.update_status(
                doc_id=doc_id,
                status="completed",
                total_chunks=len(chunks),
                summary=summary,
                error_message=None,
            )
            return True

        except Exception as e:
            self.metadata_store.update_status(doc_id, "failed", error_message=str(e))
            raise e

    async def _generate_summary(self, text: str) -> str:
        """Generate a short document summary."""
        try:
            content_sample = text[:2000]
            prompt = f"""Summarize the following document in 2-3 sentences. Focus on the main topic and key points.

Document content:
{content_sample}

Summary (2-3 sentences):"""
            summary = await self.llm_service.generate(prompt)
            return summary.strip()
        except Exception as e:
            print(f"Failed to generate summary: {e}")
            return "Summary generation failed."

    async def list_documents(self) -> List[DocumentResponse]:
        """List all persisted documents."""
        return [
            self._record_to_response(record)
            for record in self.metadata_store.list_documents()
        ]

    async def get_document(self, doc_id: str) -> Optional[DocumentResponse]:
        """Get one document by ID."""
        record = self.metadata_store.get_document(doc_id)
        if not record:
            return None
        return self._record_to_response(record)

    async def delete_document(self, doc_id: str) -> bool:
        """Delete document metadata, source file, and vectors."""
        record = self.metadata_store.get_document(doc_id)
        if not record:
            return False

        source_path = record.get("source_path")
        if source_path and os.path.exists(source_path):
            os.remove(source_path)

        await self.vector_store.delete_document(doc_id)
        self.metadata_store.delete_document(doc_id)
        return True

    async def get_document_status(self, doc_id: str) -> Optional[dict]:
        """Get document processing status."""
        record = self.metadata_store.get_document(doc_id)
        if not record:
            return None

        return {
            "doc_id": doc_id,
            "status": record["status"],
            "total_chunks": record["total_chunks"],
            "error_message": record["error_message"],
        }

    def _record_to_response(self, record: dict) -> DocumentResponse:
        upload_time = datetime.fromisoformat(record["upload_time"])
        return DocumentResponse(
            doc_id=record["doc_id"],
            filename=record["filename"],
            file_type=record["file_type"],
            upload_time=upload_time,
            status=record["status"],
            total_chunks=record["total_chunks"],
            summary=record["summary"],
        )
