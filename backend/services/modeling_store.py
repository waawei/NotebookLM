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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    source_run_id TEXT,
                    source_experiment_id TEXT,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(project_id, relative_path, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_requests (
                    approval_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    gate TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_decisions (
                    decision_id TEXT PRIMARY KEY,
                    approval_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TEXT NOT NULL
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

    def transition_state(
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
            cursor = conn.execute(
                """
                UPDATE modeling_projects
                SET state = ?, updated_at = ?
                WHERE project_id = ?
                """,
                (to_state, datetime.now().isoformat(), project_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Modeling project not found")

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
        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task.pop("input_payload_json"))
            task["output_requirements"] = json.loads(task.pop("output_requirements_json"))
            tasks.append(task)
        return tasks

    def create_artifact(
        self,
        project_id: str,
        artifact_type: str,
        relative_path: str,
        sha256: str,
        source_run_id: str | None,
        source_experiment_id: str | None,
        version: int,
    ) -> dict:
        artifact = {
            "artifact_id": str(uuid.uuid4()),
            "project_id": project_id,
            "artifact_type": artifact_type,
            "relative_path": relative_path,
            "sha256": sha256,
            "source_run_id": source_run_id,
            "source_experiment_id": source_experiment_id,
            "version": version,
            "created_at": datetime.now().isoformat(),
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO project_artifacts (
                    artifact_id, project_id, artifact_type, relative_path,
                    sha256, source_run_id, source_experiment_id, version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(artifact.values()),
            )
        return artifact

    def list_artifacts(self, project_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM project_artifacts
                WHERE project_id = ?
                ORDER BY created_at, version
                """,
                (project_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_artifact(self, artifact_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM project_artifacts WHERE artifact_id = ?",
                (artifact_id,),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _approval_from_row(row) -> dict | None:
        if not row:
            return None
        approval = dict(row)
        approval["payload"] = json.loads(approval.pop("payload_json"))
        return approval

    def create_approval_request(
        self, project_id: str, gate: str, payload: dict, payload_hash: str
    ) -> dict:
        now = datetime.now().isoformat()
        request = {
            "approval_id": str(uuid.uuid4()),
            "project_id": project_id,
            "gate": gate,
            "payload_json": json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            "payload_hash": payload_hash,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO approval_requests (
                    approval_id, project_id, gate, payload_json, payload_hash,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(request.values()),
            )
        return self._approval_from_row(request)

    def get_approval_request(self, approval_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM approval_requests WHERE approval_id = ?",
                (approval_id,),
            ).fetchone()
        return self._approval_from_row(row)

    def create_approval_decision(
        self,
        approval_id: str,
        decision: str,
        payload_hash: str,
        comment: str,
    ) -> dict:
        now = datetime.now().isoformat()
        item = {
            "decision_id": str(uuid.uuid4()),
            "approval_id": approval_id,
            "decision": decision,
            "payload_hash": payload_hash,
            "comment": comment,
            "created_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO approval_decisions (
                    decision_id, approval_id, decision, payload_hash, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
            conn.execute(
                """
                UPDATE approval_requests
                SET status = ?, updated_at = ?
                WHERE approval_id = ?
                """,
                (decision, now, approval_id),
            )
        return item

    def find_approved_request(
        self, project_id: str, gate: str, payload_hash: str
    ) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT d.* FROM approval_decisions AS d
                JOIN approval_requests AS r ON r.approval_id = d.approval_id
                WHERE r.project_id = ? AND r.gate = ?
                  AND r.payload_hash = ? AND d.payload_hash = ?
                  AND d.decision = 'approved'
                ORDER BY d.created_at DESC
                LIMIT 1
                """,
                (project_id, gate, payload_hash, payload_hash),
            ).fetchone()
        return dict(row) if row else None
