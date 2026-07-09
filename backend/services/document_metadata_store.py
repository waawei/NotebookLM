"""
SQLite persistence for user-facing document metadata.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional

from core.config import settings
from models.document import DocumentMetadata


class DocumentMetadataStore:
    """Small SQLite store for document metadata and processing status."""

    def __init__(self, db_path: Optional[str] = None):
        data_dir = os.path.dirname(settings.UPLOAD_DIR) or "."
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = db_path or os.path.join(data_dir, "notebooklm.db")
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_chunks INTEGER NOT NULL DEFAULT 0,
                    summary TEXT,
                    error_message TEXT,
                    source_type TEXT NOT NULL DEFAULT 'file',
                    source_path TEXT,
                    source_url TEXT
                )
                """
            )

    def upsert_document(
        self,
        metadata: DocumentMetadata,
        source_path: Optional[str] = None,
        source_url: Optional[str] = None,
        source_type: str = "file",
    ):
        upload_time = metadata.upload_time
        if isinstance(upload_time, datetime):
            upload_time = upload_time.isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    doc_id, filename, file_type, file_size, upload_time, status,
                    total_chunks, summary, error_message, source_type, source_path, source_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    filename=excluded.filename,
                    file_type=excluded.file_type,
                    file_size=excluded.file_size,
                    upload_time=excluded.upload_time,
                    status=excluded.status,
                    total_chunks=excluded.total_chunks,
                    summary=excluded.summary,
                    error_message=excluded.error_message,
                    source_type=excluded.source_type,
                    source_path=excluded.source_path,
                    source_url=excluded.source_url
                """,
                (
                    metadata.doc_id,
                    metadata.filename,
                    metadata.file_type,
                    metadata.file_size,
                    upload_time,
                    metadata.status,
                    metadata.total_chunks,
                    metadata.summary,
                    metadata.error_message,
                    source_type,
                    source_path,
                    source_url,
                ),
            )

    def get_document(self, doc_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()
        return self._row_to_dict(row)

    def list_documents(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY upload_time DESC"
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row is not None]

    def update_status(
        self,
        doc_id: str,
        status: str,
        total_chunks: Optional[int] = None,
        summary: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        current = self.get_document(doc_id)
        if not current:
            return

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE documents
                SET status = ?,
                    total_chunks = ?,
                    summary = ?,
                    error_message = ?
                WHERE doc_id = ?
                """,
                (
                    status,
                    current["total_chunks"] if total_chunks is None else total_chunks,
                    current["summary"] if summary is None else summary,
                    error_message,
                    doc_id,
                ),
            )

    def delete_document(self, doc_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            return cursor.rowcount > 0

    def _row_to_dict(self, row) -> Optional[dict]:
        if row is None:
            return None
        return dict(row)
