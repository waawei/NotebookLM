import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime

from services.modeling_state import INITIAL_STATE


class ModelingStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS modeling_projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT NOT NULL UNIQUE,
                    workspace_path TEXT NOT NULL UNIQUE,
                    state TEXT NOT NULL,
                    deadline TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_transitions (
                    transition_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_tasks (
                    task_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_payload_json TEXT NOT NULL,
                    output_requirements_json TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create_project(
        self,
        name: str,
        slug: str,
        workspace_path: str,
        deadline: str | None,
    ) -> dict:
        now = datetime.now().isoformat()
        project = {
            "project_id": str(uuid.uuid4()),
            "name": name,
            "slug": slug,
            "workspace_path": workspace_path,
            "state": INITIAL_STATE,
            "deadline": deadline,
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO modeling_projects (
                    project_id, name, slug, workspace_path, state, deadline,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project["project_id"],
                    project["name"],
                    project["slug"],
                    project["workspace_path"],
                    project["state"],
                    project["deadline"],
                    project["created_at"],
                    project["updated_at"],
                ),
            )
        return project

    def list_projects(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM modeling_projects ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM modeling_projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_state(self, project_id: str, state: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE modeling_projects
                SET state = ?, updated_at = ?
                WHERE project_id = ?
                """,
                (state, datetime.now().isoformat(), project_id),
            )

    def record_transition(
        self,
        project_id: str,
        from_state: str,
        to_state: str,
        reason: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_transitions (
                    transition_id, project_id, from_state, to_state, reason, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    project_id,
                    from_state,
                    to_state,
                    reason,
                    datetime.now().isoformat(),
                ),
            )

    def list_transitions(self, project_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM workflow_transitions
                WHERE project_id = ?
                ORDER BY created_at
                """,
                (project_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_task(
        self,
        project_id: str,
        stage: str,
        role: str,
        input_payload: dict,
        output_requirements: list[str],
    ) -> dict:
        now = datetime.now().isoformat()
        task = {
            "task_id": str(uuid.uuid4()),
            "project_id": project_id,
            "stage": stage,
            "role": role,
            "status": "pending",
            "input_payload": input_payload,
            "output_requirements": output_requirements,
            "retry_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_tasks (
                    task_id, project_id, stage, role, status, input_payload_json,
                    output_requirements_json, retry_count, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task["task_id"],
                    project_id,
                    stage,
                    role,
                    task["status"],
                    json.dumps(input_payload, ensure_ascii=False),
                    json.dumps(output_requirements, ensure_ascii=False),
                    task["retry_count"],
                    now,
                    now,
                ),
            )
        return task

    def update_task(self, task_id: str, status: str, retry_count: int) -> None:
        if status not in {"pending", "running", "completed", "failed", "blocked", "cancelled"}:
            raise ValueError("Invalid workflow task status")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE workflow_tasks
                SET status = ?, retry_count = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (status, retry_count, datetime.now().isoformat(), task_id),
            )

    def list_tasks(self, project_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM workflow_tasks
                WHERE project_id = ?
                ORDER BY created_at
                """,
                (project_id,),
            ).fetchall()
        return [
            {
                **dict(row),
                "input_payload": json.loads(row["input_payload_json"]),
                "output_requirements": json.loads(row["output_requirements_json"]),
            }
            for row in rows
        ]
