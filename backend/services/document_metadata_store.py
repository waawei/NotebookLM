"""
SQLite persistence for user-facing document metadata.
"""

import os
import json
import sqlite3
import uuid
from contextlib import contextmanager
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

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            conn.close()

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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS spaces (
                    space_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_spaces (
                    doc_id TEXT NOT NULL,
                    space_id TEXT NOT NULL,
                    PRIMARY KEY (doc_id, space_id),
                    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
                    FOREIGN KEY (space_id) REFERENCES spaces(space_id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_tags (
                    doc_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (doc_id, tag),
                    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
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
        return [self._decorate_document(row) for row in rows if row is not None]

    def create_space(self, name: str, description: str = "") -> dict:
        now = datetime.now().isoformat()
        space = {
            "space_id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO spaces (space_id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    space["space_id"],
                    space["name"],
                    space["description"],
                    space["created_at"],
                    space["updated_at"],
                ),
            )
        return space

    def list_spaces(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM spaces ORDER BY updated_at DESC, name ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_space(self, space_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM spaces WHERE space_id = ?",
                (space_id,),
            ).fetchone()
        return self._row_to_dict(row)

    def update_space(
        self,
        space_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        current = self.get_space(space_id)
        if not current:
            return None

        updated = {
            **current,
            "name": current["name"] if name is None else name,
            "description": current["description"] if description is None else description,
            "updated_at": datetime.now().isoformat(),
        }
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE spaces
                SET name = ?, description = ?, updated_at = ?
                WHERE space_id = ?
                """,
                (
                    updated["name"],
                    updated["description"],
                    updated["updated_at"],
                    space_id,
                ),
            )
        return updated

    def delete_space(self, space_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM spaces WHERE space_id = ?", (space_id,))
            return cursor.rowcount > 0

    def assign_document_to_space(self, doc_id: str, space_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO document_spaces (doc_id, space_id)
                VALUES (?, ?)
                """,
                (doc_id, space_id),
            )

    def set_document_tags(self, doc_id: str, tags: list[str]) -> None:
        normalized_tags = []
        seen = set()
        for tag in tags:
            normalized = tag.strip()
            if normalized and normalized not in seen:
                normalized_tags.append(normalized)
                seen.add(normalized)

        with self._connect() as conn:
            conn.execute("DELETE FROM document_tags WHERE doc_id = ?", (doc_id,))
            conn.executemany(
                "INSERT INTO document_tags (doc_id, tag) VALUES (?, ?)",
                [(doc_id, tag) for tag in normalized_tags],
            )

    def search_documents(
        self,
        query: str = "",
        space_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        clauses = []
        params = []

        if query:
            clauses.append(
                """
                (
                    d.filename LIKE ?
                    OR COALESCE(d.summary, '') LIKE ?
                    OR COALESCE(d.source_path, '') LIKE ?
                    OR COALESCE(d.source_url, '') LIKE ?
                )
                """
            )
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query, like_query])

        if space_id:
            clauses.append(
                """
                EXISTS (
                    SELECT 1 FROM document_spaces ds_filter
                    WHERE ds_filter.doc_id = d.doc_id AND ds_filter.space_id = ?
                )
                """
            )
            params.append(space_id)

        if status:
            clauses.append("d.status = ?")
            params.append(status)

        for tag in tags or []:
            clauses.append(
                """
                EXISTS (
                    SELECT 1 FROM document_tags dt_filter
                    WHERE dt_filter.doc_id = d.doc_id AND dt_filter.tag = ?
                )
                """
            )
            params.append(tag)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT d.*
                FROM documents d
                {where_sql}
                ORDER BY d.upload_time DESC
                """,
                params,
            ).fetchall()

        return [self._decorate_document(row, selected_space_id=space_id) for row in rows]

    def save_conversation(self, conversation: dict) -> None:
        conversation_id = conversation.get("conversation_id") or conversation.get("id")
        if not conversation_id:
            raise ValueError("conversation_id is required")

        now = datetime.now().isoformat()
        created_at = self._to_iso_string(conversation.get("created_at") or now)
        updated_at = self._to_iso_string(conversation.get("updated_at") or now)
        title = conversation.get("title") or self._conversation_title(conversation)
        messages = conversation.get("messages", [])

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations (conversation_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    title=excluded.title,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at
                """,
                (conversation_id, title, created_at, updated_at),
            )
            conn.execute(
                "DELETE FROM conversation_messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            conn.executemany(
                """
                INSERT INTO conversation_messages (
                    message_id, conversation_id, role, content, citations_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        message.get("message_id") or str(uuid.uuid4()),
                        conversation_id,
                        message["role"],
                        message["content"],
                        json.dumps(message.get("citations", []), ensure_ascii=False),
                        self._to_iso_string(message.get("created_at") or now),
                    )
                    for message in messages
                ],
            )

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        with self._connect() as conn:
            conversation_row = conn.execute(
                """
                SELECT *
                FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()
            message_rows = conn.execute(
                """
                SELECT *
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC, message_id ASC
                """,
                (conversation_id,),
            ).fetchall()

        if conversation_row is None:
            return None

        conversation = dict(conversation_row)
        conversation["messages"] = [
            {
                "message_id": row["message_id"],
                "role": row["role"],
                "content": row["content"],
                "citations": json.loads(row["citations_json"]),
                "created_at": row["created_at"],
            }
            for row in message_rows
        ]
        return conversation

    def list_conversations(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    c.conversation_id,
                    c.title,
                    c.created_at,
                    c.updated_at,
                    COUNT(cm.message_id) AS message_count,
                    (
                        SELECT content
                        FROM conversation_messages latest
                        WHERE latest.conversation_id = c.conversation_id
                        ORDER BY latest.created_at DESC, latest.message_id DESC
                        LIMIT 1
                    ) AS last_message
                FROM conversations c
                LEFT JOIN conversation_messages cm
                    ON cm.conversation_id = c.conversation_id
                GROUP BY c.conversation_id, c.title, c.created_at, c.updated_at
                ORDER BY c.updated_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_conversation(self, conversation_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            )
            return cursor.rowcount > 0

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

    def _decorate_document(
        self,
        row,
        selected_space_id: Optional[str] = None,
    ) -> Optional[dict]:
        document = self._row_to_dict(row)
        if document is None:
            return None

        with self._connect() as conn:
            tag_rows = conn.execute(
                """
                SELECT tag
                FROM document_tags
                WHERE doc_id = ?
                ORDER BY tag ASC
                """,
                (document["doc_id"],),
            ).fetchall()
            space_rows = conn.execute(
                """
                SELECT space_id
                FROM document_spaces
                WHERE doc_id = ?
                ORDER BY space_id ASC
                """,
                (document["doc_id"],),
            ).fetchall()

        space_ids = [space_row["space_id"] for space_row in space_rows]
        document["tags"] = [tag_row["tag"] for tag_row in tag_rows]
        document["space_ids"] = space_ids
        document["space_id"] = selected_space_id or (space_ids[0] if space_ids else None)
        return document

    def _to_iso_string(self, value) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _conversation_title(self, conversation: dict) -> str:
        for message in conversation.get("messages", []):
            if message.get("role") == "user" and message.get("content"):
                return message["content"][:80]
        return "Untitled conversation"
