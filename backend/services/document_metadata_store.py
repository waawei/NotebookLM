"""
SQLite persistence for user-facing document metadata.
"""

import os
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from core.config import settings
from models.document import DocumentMetadata


_UNSET = object()


class DocumentMetadataStore:
    """Small SQLite store for document metadata and processing status."""

    _SENSITIVE_AGENT_FIELD_NAMES = frozenset(
        {
            "apikey",
            "authorization",
            "accesstoken",
            "refreshtoken",
            "token",
            "secret",
            "password",
        }
    )
    _BEARER_TOKEN_PATTERN = re.compile(r"\bbearer\s+[^\s,;]+", re.IGNORECASE)
    _KEY_LIKE_TOKEN_PATTERN = re.compile(
        r"(?<![A-Za-z0-9_-])(?:sk|rk|pk|api|key)[_-][A-Za-z0-9][A-Za-z0-9_-]{7,}(?![A-Za-z0-9_-])",
        re.IGNORECASE,
    )

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
                    summary_status TEXT NOT NULL DEFAULT 'pending',
                    summary_error TEXT,
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS note_links (
                    note_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    PRIMARY KEY (note_id, source_type, source_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    note_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    doc_ids_json TEXT NOT NULL,
                    conversation_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS wiki_pages (
                    page_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_doc_ids_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outputs (
                    output_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_doc_ids_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._ensure_document_column(
                conn, "summary_status", "TEXT NOT NULL DEFAULT 'pending'"
            )
            self._ensure_document_column(conn, "summary_error", "TEXT")
            conn.execute(
                """
                UPDATE documents
                SET summary = NULL,
                    summary_status = 'unavailable',
                    summary_error = 'LLM summary unavailable'
                WHERE summary = 'Summary generation failed.'
                """
            )
            conn.execute(
                """
                UPDATE documents
                SET summary_status = 'available'
                WHERE summary_status = 'pending' AND summary IS NOT NULL
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_payload_json TEXT NOT NULL,
                    output_id TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_steps (
                    step_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES agent_runs(run_id) ON DELETE CASCADE
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
                    total_chunks, summary, summary_status, summary_error, error_message,
                    source_type, source_path, source_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    filename=excluded.filename,
                    file_type=excluded.file_type,
                    file_size=excluded.file_size,
                    upload_time=excluded.upload_time,
                    status=excluded.status,
                    total_chunks=excluded.total_chunks,
                    summary=excluded.summary,
                    summary_status=excluded.summary_status,
                    summary_error=excluded.summary_error,
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
                    metadata.summary_status,
                    metadata.summary_error,
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

    def save_note_link(self, note_id: str, source_type: str, source_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO note_links (note_id, source_type, source_id)
                VALUES (?, ?, ?)
                """,
                (note_id, source_type, source_id),
            )

    def list_note_links(self, note_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT source_type, source_id
                FROM note_links
                WHERE note_id = ?
                ORDER BY source_type ASC, source_id ASC
                """,
                (note_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def clear_note_links(self, note_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM note_links WHERE note_id = ?", (note_id,))

    def save_note(self, note: dict) -> None:
        note_id = note["note_id"]
        created_at = self._to_iso_string(note["created_at"])
        updated_at = self._to_iso_string(note["updated_at"])
        doc_ids = note.get("doc_ids") or []
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO notes (
                    note_id, title, content, doc_ids_json, conversation_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(note_id) DO UPDATE SET
                    title=excluded.title,
                    content=excluded.content,
                    doc_ids_json=excluded.doc_ids_json,
                    conversation_id=excluded.conversation_id,
                    updated_at=excluded.updated_at
                """,
                (
                    note_id,
                    note["title"],
                    note["content"],
                    json.dumps(doc_ids, ensure_ascii=False),
                    note.get("conversation_id"),
                    created_at,
                    updated_at,
                ),
            )

    def get_note(self, note_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE note_id = ?",
                (note_id,),
            ).fetchone()
        return self._note_row_to_dict(row)

    def list_notes(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM notes ORDER BY updated_at DESC"
            ).fetchall()
        return [self._note_row_to_dict(row) for row in rows]

    def delete_note(self, note_id: str) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM note_links WHERE note_id = ?", (note_id,))
            cursor = conn.execute("DELETE FROM notes WHERE note_id = ?", (note_id,))
            return cursor.rowcount > 0

    def create_wiki_page(
        self,
        title: str,
        content: str,
        source_doc_ids: list[str],
    ) -> dict:
        now = datetime.now().isoformat()
        page = {
            "page_id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "source_doc_ids": source_doc_ids,
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO wiki_pages (
                    page_id, title, content, source_doc_ids_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    page["page_id"],
                    page["title"],
                    page["content"],
                    json.dumps(page["source_doc_ids"], ensure_ascii=False),
                    page["created_at"],
                    page["updated_at"],
                ),
            )
        return page

    def update_wiki_page(self, page_id: str, title: str, content: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE wiki_pages
                SET title = ?, content = ?, updated_at = ?
                WHERE page_id = ?
                """,
                (title, content, datetime.now().isoformat(), page_id),
            )
            return cursor.rowcount > 0

    def get_wiki_page(self, page_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM wiki_pages WHERE page_id = ?",
                (page_id,),
            ).fetchone()
        return self._artifact_row_to_dict(row, "page_id", "source_doc_ids_json")

    def list_wiki_pages(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM wiki_pages ORDER BY updated_at DESC"
            ).fetchall()
        return [
            self._artifact_row_to_dict(row, "page_id", "source_doc_ids_json")
            for row in rows
        ]

    def create_output(
        self,
        kind: str,
        title: str,
        content: str,
        source_doc_ids: list[str],
    ) -> dict:
        now = datetime.now().isoformat()
        output = {
            "output_id": str(uuid.uuid4()),
            "kind": kind,
            "title": title,
            "content": content,
            "source_doc_ids": source_doc_ids,
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO outputs (
                    output_id, kind, title, content, source_doc_ids_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    output["output_id"],
                    output["kind"],
                    output["title"],
                    output["content"],
                    json.dumps(output["source_doc_ids"], ensure_ascii=False),
                    output["created_at"],
                    output["updated_at"],
                ),
            )
        return output

    def list_outputs(self, kind: Optional[str] = None) -> list[dict]:
        params = []
        where_sql = ""
        if kind:
            where_sql = "WHERE kind = ?"
            params.append(kind)

        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM outputs
                {where_sql}
                ORDER BY updated_at DESC
                """,
                params,
            ).fetchall()

        return [
            self._artifact_row_to_dict(row, "output_id", "source_doc_ids_json")
            for row in rows
        ]

    def get_output(self, output_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM outputs WHERE output_id = ?",
                (output_id,),
            ).fetchone()
        return self._artifact_row_to_dict(row, "output_id", "source_doc_ids_json")

    def delete_output(self, output_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM outputs WHERE output_id = ?",
                (output_id,),
            )
            return cursor.rowcount > 0

    def create_agent_run(self, skill_id: str, input_payload: dict) -> dict:
        now = datetime.now().isoformat()
        run = {
            "run_id": str(uuid.uuid4()),
            "skill_id": skill_id,
            "status": "running",
            "input_payload": self._redact_agent_data(input_payload),
            "output_id": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "steps": [],
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_runs (
                    run_id, skill_id, status, input_payload_json, output_id, error,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run["run_id"],
                    run["skill_id"],
                    run["status"],
                    json.dumps(run["input_payload"], ensure_ascii=False),
                    run["output_id"],
                    run["error"],
                    run["created_at"],
                    run["updated_at"],
                ),
            )
        return run

    def append_agent_step(self, run_id: str, step: dict) -> None:
        kind = step.get("kind")
        title = step.get("title")
        if not isinstance(kind, str) or not kind:
            raise ValueError("Agent step kind is required")
        if not isinstance(title, str) or not title:
            raise ValueError("Agent step title is required")
        payload = self._redact_agent_data(step.get("payload", {}))

        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(step_index), -1) AS last_index FROM agent_steps WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if conn.execute(
                "SELECT 1 FROM agent_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone() is None:
                raise ValueError(f"Agent run {run_id} does not exist")
            conn.execute(
                """
                INSERT INTO agent_steps (
                    step_id, run_id, step_index, kind, title, payload_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    run_id,
                    row["last_index"] + 1,
                    kind,
                    title,
                    json.dumps(payload, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )

    def update_agent_run_status(
        self,
        run_id: str,
        status: str,
        output_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        error = self._redact_agent_data(error)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE agent_runs
                SET status = ?, output_id = ?, error = ?, updated_at = ?
                WHERE run_id = ?
                """,
                (status, output_id, error, datetime.now().isoformat(), run_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Agent run {run_id} does not exist")

    def get_agent_run(self, run_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM agent_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            step_rows = conn.execute(
                """
                SELECT * FROM agent_steps
                WHERE run_id = ?
                ORDER BY step_index ASC, step_id ASC
                """,
                (run_id,),
            ).fetchall()
        return self._agent_run_row_to_dict(row, step_rows)

    def list_agent_runs(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT run_id FROM agent_runs ORDER BY updated_at DESC, run_id ASC"
            ).fetchall()
        return [self.get_agent_run(row["run_id"]) for row in rows]

    def update_status(
        self,
        doc_id: str,
        status: str,
        total_chunks: Optional[int] = None,
        summary: object = _UNSET,
        summary_status: Optional[str] = None,
        summary_error: Optional[str] = None,
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
                    summary_status = ?,
                    summary_error = ?,
                    error_message = ?
                WHERE doc_id = ?
                """,
                (
                    status,
                    current["total_chunks"] if total_chunks is None else total_chunks,
                    current["summary"] if summary is _UNSET else summary,
                    current["summary_status"] if summary_status is None else summary_status,
                    summary_error,
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

    @staticmethod
    def _ensure_document_column(conn, name: str, definition: str) -> None:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(documents)").fetchall()
        }
        if name not in columns:
            conn.execute(f"ALTER TABLE documents ADD COLUMN {name} {definition}")

    def _artifact_row_to_dict(
        self,
        row,
        id_key: str,
        source_json_key: str,
    ) -> Optional[dict]:
        artifact = self._row_to_dict(row)
        if artifact is None:
            return None

        artifact["source_doc_ids"] = json.loads(artifact.pop(source_json_key))
        return artifact

    def _note_row_to_dict(self, row) -> Optional[dict]:
        note = self._row_to_dict(row)
        if note is None:
            return None
        note["doc_ids"] = json.loads(note.pop("doc_ids_json"))
        note["links"] = self.list_note_links(note["note_id"])
        return note

    def _agent_run_row_to_dict(self, row, step_rows) -> Optional[dict]:
        run = self._row_to_dict(row)
        if run is None:
            return None
        run["input_payload"] = json.loads(run.pop("input_payload_json"))
        run["steps"] = [
            {
                "step_id": step["step_id"],
                "step_index": step["step_index"],
                "kind": step["kind"],
                "title": step["title"],
                "payload": json.loads(step["payload_json"]),
                "created_at": step["created_at"],
            }
            for step in step_rows
        ]
        return run

    @classmethod
    def _redact_agent_data(cls, value):
        if isinstance(value, dict):
            return {
                key: "***"
                if cls._is_sensitive_agent_field(key)
                else cls._redact_agent_data(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._redact_agent_data(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._redact_agent_data(item) for item in value)
        if isinstance(value, str):
            value = cls._BEARER_TOKEN_PATTERN.sub("Bearer ***", value)
            return cls._KEY_LIKE_TOKEN_PATTERN.sub("***", value)
        return value

    @classmethod
    def _is_sensitive_agent_field(cls, name) -> bool:
        if not isinstance(name, str):
            return False
        normalized = re.sub(r"[^a-z0-9]", "", name.lower())
        return normalized in cls._SENSITIVE_AGENT_FIELD_NAMES

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
