# Mathematical Modeling Phase 1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add durable modeling projects, a validated workflow state machine, safe independent workspace creation, REST endpoints, and a usable frontend project module.

**Architecture:** Introduce a focused modeling store beside the existing document store instead of enlarging `DocumentMetadataStore`. A project service composes the store, pure state machine, and workspace service; FastAPI and React remain thin adapters.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic, SQLite, pathlib, subprocess, React 18, TypeScript, Zustand, Vitest, Testing Library.

## Global Constraints

- Follow all global constraints in `docs/superpowers/plans/2026-07-10-mathematical-modeling-roadmap.md`.
- This phase does not call an LLM, import competition files, run generated Python, compile LaTeX, or commit a generated project.
- The default workspace root is the absolute sibling directory `NotebookLM-modeling-projects` next to the application repository, configurable through `MODELING_WORKSPACE_ROOT`; its resolved path must remain outside the application source tree regardless of process working directory.
- Project slugs contain lowercase ASCII letters, digits, and hyphens only; project IDs are UUID strings.
- State transitions use the exact names declared in the roadmap.

---

## File Map

- Create `backend/services/modeling_state.py`: pure transition table and validation.
- Create `backend/services/modeling_store.py`: modeling SQLite schema and CRUD.
- Modify `backend/services/document_metadata_store.py`: optional project/task/stage links on existing Agent runs.
- Create `backend/services/modeling_workspace.py`: safe directory and repository initialization.
- Create `backend/services/modeling_project_service.py`: project orchestration facade.
- Create `backend/api/modeling.py`: Pydantic request models and routes.
- Create `backend/tests/test_modeling_state.py`.
- Create `backend/tests/test_modeling_store.py`.
- Modify `backend/tests/test_agent_store.py`.
- Create `backend/tests/test_modeling_workspace.py`.
- Create `backend/tests/test_modeling_project_service.py`.
- Create `backend/tests/test_modeling_api.py`.
- Modify `backend/core/config.py`: add workspace root.
- Modify `backend/main.py`: mount modeling router.
- Modify `frontend/src/services/api.ts`: add modeling types/client.
- Modify `frontend/src/store/useStore.ts`: add `modeling` module and selected project ID.
- Modify `frontend/src/i18n.ts`: add English and Chinese modeling labels.
- Modify `frontend/src/components/ModuleNav.tsx`: add modeling rail item.
- Modify `frontend/src/App.tsx`: render modeling view.
- Create `frontend/src/views/ModelingProjectsView.tsx`.
- Create `frontend/src/views/ModelingProjectsView.test.tsx`.
- Modify `frontend/src/services/api.test.ts`, `frontend/src/store/useStore.test.ts`, and `frontend/src/components/ModuleNav.test.tsx`.

### Task 1: Pure Workflow State Machine

**Files:**
- Create: `backend/services/modeling_state.py`
- Test: `backend/tests/test_modeling_state.py`

**Interfaces:**
- Produces: `INITIAL_STATE`, `TERMINAL_STATE`, `WorkflowTransitionError`, `next_state(current: str) -> str`, and `previous_state(current: str) -> str`.
- Consumes: no filesystem, database, or service dependencies.

- [ ] **Step 1: Write failing transition tests**

```python
import unittest

from services.modeling_state import WorkflowTransitionError, next_state, previous_state


class ModelingStateTests(unittest.TestCase):
    def test_advances_only_to_declared_successor(self):
        self.assertEqual(next_state("project_initialized"), "problem_parsing")
        self.assertEqual(next_state("model_approval_pending"), "experiment_implementation")

    def test_completed_project_cannot_advance(self):
        with self.assertRaises(WorkflowTransitionError):
            next_state("completed")

    def test_rollback_uses_declared_editable_predecessor(self):
        self.assertEqual(previous_state("model_approval_pending"), "model_planning")
        self.assertEqual(previous_state("execution_approval_pending"), "experiment_implementation")

    def test_unknown_state_is_rejected(self):
        with self.assertRaises(WorkflowTransitionError):
            next_state("made_up")
```

- [ ] **Step 2: Run the state tests and verify import failure**

Run: `python -m pytest backend/tests/test_modeling_state.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'services.modeling_state'`.

- [ ] **Step 3: Implement the explicit transition table**

```python
from typing import Final


class WorkflowTransitionError(ValueError):
    """Raised when a project requests an illegal workflow transition."""


STATES: Final[tuple[str, ...]] = (
    "project_initialized", "problem_parsing", "data_profiling", "model_planning",
    "model_approval_pending", "experiment_implementation", "execution_approval_pending",
    "experiment_running", "result_validation", "paper_drafting", "consistency_review",
    "final_approval_pending", "packaging", "commit_approval_pending", "committing", "completed",
)
INITIAL_STATE: Final[str] = STATES[0]
TERMINAL_STATE: Final[str] = STATES[-1]
_NEXT: Final[dict[str, str]] = dict(zip(STATES, STATES[1:]))
_ROLLBACK: Final[dict[str, str]] = {
    "problem_parsing": "project_initialized",
    "data_profiling": "problem_parsing",
    "model_planning": "data_profiling",
    "model_approval_pending": "model_planning",
    "experiment_implementation": "model_planning",
    "execution_approval_pending": "experiment_implementation",
    "experiment_running": "experiment_implementation",
    "result_validation": "experiment_implementation",
    "paper_drafting": "result_validation",
    "consistency_review": "paper_drafting",
    "final_approval_pending": "paper_drafting",
    "packaging": "paper_drafting",
    "commit_approval_pending": "packaging",
    "committing": "packaging",
}


def next_state(current: str) -> str:
    try:
        return _NEXT[current]
    except KeyError as exc:
        raise WorkflowTransitionError(f"Cannot advance workflow state: {current}") from exc


def previous_state(current: str) -> str:
    try:
        return _ROLLBACK[current]
    except KeyError as exc:
        raise WorkflowTransitionError(f"Cannot roll back workflow state: {current}") from exc
```

- [ ] **Step 4: Run the state tests**

Run: `python -m pytest backend/tests/test_modeling_state.py -q`

Expected: `4 passed`.

- [ ] **Step 5: Commit the state machine**

```powershell
git add backend/services/modeling_state.py backend/tests/test_modeling_state.py
git commit -m "feat: add modeling workflow state machine"
```

### Task 2: Modeling Metadata Store

**Files:**
- Create: `backend/services/modeling_store.py`
- Test: `backend/tests/test_modeling_store.py`
- Modify: `backend/services/document_metadata_store.py`
- Modify: `backend/tests/test_agent_store.py`

**Interfaces:**
- Consumes: workflow state strings from `modeling_state.py`.
- Produces: project/transition methods plus `create_task`, `update_task`, and `list_tasks`; existing Agent runs gain optional `project_id`, `task_id`, and `stage` links.

- [ ] **Step 1: Write failing persistence tests**

```python
import os
import tempfile
import unittest

from services.modeling_store import ModelingStore


class ModelingStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = ModelingStore(os.path.join(self.tempdir.name, "modeling.db"))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_project_and_transition_survive_new_store_instance(self):
        project = self.store.create_project("Forecast", "forecast", "D:/safe/forecast", None)
        self.store.record_transition(project["project_id"], "project_initialized", "problem_parsing", "advance")
        self.store.update_state(project["project_id"], "problem_parsing")

        reopened = ModelingStore(self.store.db_path)
        loaded = reopened.get_project(project["project_id"])
        self.assertEqual(loaded["state"], "problem_parsing")
        self.assertEqual(len(reopened.list_transitions(project["project_id"])), 1)
```

- [ ] **Step 2: Run the store test and verify failure**

Run: `python -m pytest backend/tests/test_modeling_store.py -q`

Expected: FAIL because `ModelingStore` does not exist.

- [ ] **Step 3: Implement the focused SQLite store**

```python
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
            conn.execute("CREATE TABLE IF NOT EXISTS modeling_projects (project_id TEXT PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, workspace_path TEXT NOT NULL UNIQUE, state TEXT NOT NULL, deadline TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS workflow_transitions (transition_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, from_state TEXT NOT NULL, to_state TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS workflow_tasks (task_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, stage TEXT NOT NULL, role TEXT NOT NULL, status TEXT NOT NULL, input_payload_json TEXT NOT NULL, output_requirements_json TEXT NOT NULL, retry_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")

    def create_project(self, name: str, slug: str, workspace_path: str, deadline: str | None) -> dict:
        now = datetime.now().isoformat()
        project = {"project_id": str(uuid.uuid4()), "name": name, "slug": slug, "workspace_path": workspace_path, "state": INITIAL_STATE, "deadline": deadline, "created_at": now, "updated_at": now}
        with self._connect() as conn:
            conn.execute("INSERT INTO modeling_projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tuple(project.values()))
        return project

    def list_projects(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM modeling_projects ORDER BY updated_at DESC").fetchall()
        return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM modeling_projects WHERE project_id = ?", (project_id,)).fetchone()
        return dict(row) if row else None

    def update_state(self, project_id: str, state: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE modeling_projects SET state = ?, updated_at = ? WHERE project_id = ?", (state, datetime.now().isoformat(), project_id))

    def record_transition(self, project_id: str, from_state: str, to_state: str, reason: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO workflow_transitions VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), project_id, from_state, to_state, reason, datetime.now().isoformat()))

    def list_transitions(self, project_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM workflow_transitions WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()
        return [dict(row) for row in rows]
```

Add task methods with these exact contracts:

```python
def create_task(self, project_id: str, stage: str, role: str, input_payload: dict, output_requirements: list[str]) -> dict:
    now = datetime.now().isoformat()
    task = {"task_id": str(uuid.uuid4()), "project_id": project_id, "stage": stage, "role": role, "status": "pending", "input_payload": input_payload, "output_requirements": output_requirements, "retry_count": 0, "created_at": now, "updated_at": now}
    with self._connect() as conn:
        conn.execute("INSERT INTO workflow_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (task["task_id"], project_id, stage, role, "pending", json.dumps(input_payload, ensure_ascii=False), json.dumps(output_requirements, ensure_ascii=False), 0, now, now))
    return task

def update_task(self, task_id: str, status: str, retry_count: int) -> None:
    if status not in {"pending", "running", "completed", "failed", "blocked", "cancelled"}:
        raise ValueError("Invalid workflow task status")
    with self._connect() as conn:
        conn.execute("UPDATE workflow_tasks SET status = ?, retry_count = ?, updated_at = ? WHERE task_id = ?", (status, retry_count, datetime.now().isoformat(), task_id))

def list_tasks(self, project_id: str) -> list[dict]:
    with self._connect() as conn:
        rows = conn.execute("SELECT * FROM workflow_tasks WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()
    return [{**dict(row), "input_payload": json.loads(row["input_payload_json"]), "output_requirements": json.loads(row["output_requirements_json"])} for row in rows]
```

In `DocumentMetadataStore._init_db`, migrate existing Agent runs without breaking old rows:

```python
self._ensure_table_column(conn, "agent_runs", "project_id", "TEXT")
self._ensure_table_column(conn, "agent_runs", "task_id", "TEXT")
self._ensure_table_column(conn, "agent_runs", "stage", "TEXT")
```

Extend `create_agent_run` with optional keyword arguments `project_id=None`, `task_id=None`, and `stage=None`, persist them, and return them from `_agent_run_row_to_dict`. Add a regression assertion that the old two-argument call still returns all three links as `None`, while a modeling call round-trips supplied IDs.

- [ ] **Step 4: Run persistence tests**

Run: `python -m pytest backend/tests/test_modeling_store.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the store**

```powershell
git add backend/services/modeling_store.py backend/services/document_metadata_store.py backend/tests/test_modeling_store.py backend/tests/test_agent_store.py
git commit -m "feat: persist modeling workflow metadata"
```

### Task 3: Safe Workspace and Project Service

**Files:**
- Create: `backend/services/modeling_workspace.py`
- Create: `backend/services/modeling_project_service.py`
- Modify: `backend/core/config.py`
- Test: `backend/tests/test_modeling_workspace.py`
- Test: `backend/tests/test_modeling_project_service.py`

**Interfaces:**
- Consumes: `ModelingStore`, `next_state`, `previous_state`, and `settings.MODELING_WORKSPACE_ROOT`.
- Produces: the stable `ModelingProjectService` interface declared in the roadmap.

- [ ] **Step 1: Write failing workspace safety and service tests**

```python
def test_workspace_rejects_source_tree_parent(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    service = ModelingWorkspaceService(str(source_root), str(source_root))
    with pytest.raises(ValueError, match="outside the application source tree"):
        service.create("forecast")


def test_project_service_creates_repo_and_advances(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    workspace = ModelingWorkspaceService(str(tmp_path / "projects"), str(tmp_path / "app"))
    service = ModelingProjectService(store, workspace)
    project = service.create_project("Sales Forecast")
    advanced = service.advance(project["project_id"])
    assert advanced["state"] == "problem_parsing"
    assert (tmp_path / "projects" / project["slug"] / ".git").is_dir()
```

- [ ] **Step 2: Run both tests and verify failure**

Run: `python -m pytest backend/tests/test_modeling_workspace.py backend/tests/test_modeling_project_service.py -q`

Expected: FAIL because both services are missing.

- [ ] **Step 3: Add the workspace setting and implement safe creation**

Add these imports and constants before the existing `Settings` class:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELING_WORKSPACE_ROOT = str(PROJECT_ROOT.parent / "NotebookLM-modeling-projects")
```

Add this field inside the existing `Settings` class directly below `UPLOAD_DIR`:

```python
MODELING_WORKSPACE_ROOT: str = DEFAULT_MODELING_WORKSPACE_ROOT
```

Create `modeling_workspace.py` with:

```python
import re
import subprocess
from pathlib import Path


class ModelingWorkspaceService:
    def __init__(self, workspace_root: str, source_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.source_root = Path(source_root).resolve()

    def create(self, slug: str) -> Path:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError("Invalid project slug")
        target = (self.workspace_root / slug).resolve()
        if target == self.source_root or self.source_root in target.parents:
            raise ValueError("Modeling workspaces must be outside the application source tree")
        if target != self.workspace_root / slug or target.exists():
            raise ValueError("Project workspace already exists or escapes its root")
        target.mkdir(parents=True)
        for relative in ("problem/original", "data/raw", "analysis", "src", "tests", "experiments", "figures", "tables", "paper/sections", "deliverables", ".workflow/runs"):
            (target / relative).mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=target, check=True, capture_output=True, text=True)
        return target
```

- [ ] **Step 4: Implement project orchestration with deterministic slugs**

```python
import re

from services.document_metadata_store import DocumentMetadataStore
from services.modeling_state import next_state, previous_state


class ModelingProjectService:
    def __init__(self, store, workspace_service, agent_store=None):
        self.store = store
        self.workspace_service = workspace_service
        self.agent_store = agent_store or DocumentMetadataStore()

    @staticmethod
    def _slug(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return slug or "modeling-project"

    def create_project(self, name: str, deadline: str | None = None) -> dict:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Project name is required")
        slug = self._slug(clean_name)
        path = self.workspace_service.create(slug)
        return self.store.create_project(clean_name, slug, str(path), deadline)

    def list_projects(self) -> list[dict]:
        return self.store.list_projects()

    def get_project(self, project_id: str) -> dict | None:
        return self.store.get_project(project_id)

    def list_tasks(self, project_id: str) -> list[dict]:
        self._require(project_id)
        return self.store.list_tasks(project_id)

    def list_runs(self, project_id: str) -> list[dict]:
        self._require(project_id)
        return self.agent_store.list_agent_runs(project_id=project_id)

    def advance(self, project_id: str) -> dict:
        project = self._require(project_id)
        target = next_state(project["state"])
        self.store.record_transition(project_id, project["state"], target, "advance")
        self.store.update_state(project_id, target)
        return self._require(project_id)

    def rollback(self, project_id: str, reason: str) -> dict:
        project = self._require(project_id)
        target = previous_state(project["state"])
        self.store.record_transition(project_id, project["state"], target, reason.strip() or "rollback")
        self.store.update_state(project_id, target)
        return self._require(project_id)

    def _require(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        return project
```

- [ ] **Step 5: Run workspace and service tests**

Run: `python -m pytest backend/tests/test_modeling_workspace.py backend/tests/test_modeling_project_service.py -q`

Expected: PASS.

- [ ] **Step 6: Commit workspace and orchestration**

```powershell
git add backend/core/config.py backend/services/modeling_workspace.py backend/services/modeling_project_service.py backend/tests/test_modeling_workspace.py backend/tests/test_modeling_project_service.py
git commit -m "feat: create isolated modeling project workspaces"
```

### Task 4: Modeling REST API

**Files:**
- Create: `backend/api/modeling.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_modeling_api.py`

**Interfaces:**
- Consumes: `ModelingProjectService` methods from Task 3.
- Produces: `POST/GET /api/modeling/projects`, `GET /api/modeling/projects/{id}`, `POST /advance`, `POST /rollback`, `GET /tasks`, and `GET /runs`.

- [ ] **Step 1: Write failing API tests using a fake service**

```python
import asyncio
import unittest
from fastapi import HTTPException

from api import modeling


class FakeProjectService:
    def create_project(self, name, deadline=None):
        return {"project_id": "p-1", "name": name, "state": "project_initialized"}
    def list_projects(self):
        return [{"project_id": "p-1", "name": "Forecast", "state": "project_initialized"}]
    def get_project(self, project_id):
        return self.list_projects()[0] if project_id == "p-1" else None
    def advance(self, project_id):
        return {**self.get_project(project_id), "state": "problem_parsing"}
    def rollback(self, project_id, reason):
        return {**self.get_project(project_id), "state": "project_initialized"}
    def list_tasks(self, project_id):
        return []
    def list_runs(self, project_id):
        return []


class ModelingApiTests(unittest.TestCase):
    def setUp(self):
        self.original = modeling.project_service
        modeling.project_service = FakeProjectService()
    def tearDown(self):
        modeling.project_service = self.original
    def test_lists_and_advances_project(self):
        self.assertEqual(asyncio.run(modeling.list_projects())["total"], 1)
        result = asyncio.run(modeling.advance_project("p-1"))
        self.assertEqual(result["state"], "problem_parsing")
    def test_missing_project_returns_404(self):
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(modeling.get_project("missing"))
        self.assertEqual(raised.exception.status_code, 404)
```

- [ ] **Step 2: Run the API test and verify import failure**

Run: `python -m pytest backend/tests/test_modeling_api.py -q`

Expected: FAIL because `api.modeling` does not exist.

- [ ] **Step 3: Implement thin routes and safe error mapping**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import PROJECT_ROOT, settings
from services.modeling_project_service import ModelingProjectService
from services.modeling_store import ModelingStore
from services.modeling_workspace import ModelingWorkspaceService

router = APIRouter()
project_service = ModelingProjectService(
    ModelingStore("./data/notebooklm.db"),
    ModelingWorkspaceService(settings.MODELING_WORKSPACE_ROOT, str(PROJECT_ROOT)),
)


class ProjectCreate(BaseModel):
    name: str
    deadline: str | None = None


class RollbackRequest(BaseModel):
    reason: str


@router.post("/projects")
async def create_project(request: ProjectCreate):
    try:
        return project_service.create_project(request.name, request.deadline)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects")
async def list_projects():
    projects = project_service.list_projects()
    return {"projects": projects, "total": len(projects)}


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Modeling project not found")
    return project


@router.post("/projects/{project_id}/advance")
async def advance_project(project_id: str):
    try:
        return project_service.advance(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/projects/{project_id}/rollback")
async def rollback_project(project_id: str, request: RollbackRequest):
    try:
        return project_service.rollback(project_id, request.reason)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/projects/{project_id}/tasks")
async def list_project_tasks(project_id: str):
    tasks = project_service.list_tasks(project_id)
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/projects/{project_id}/runs")
async def list_project_runs(project_id: str):
    runs = project_service.list_runs(project_id)
    return {"runs": runs, "total": len(runs)}
```

Implement `ModelingProjectService.list_tasks` by delegating to `ModelingStore.list_tasks`. Inject `DocumentMetadataStore` into the service and implement `list_runs` by calling its new `list_agent_runs(project_id=project_id)` filter; retain no-argument behavior for the existing Agents page.

Mount it in `backend/main.py`:

```python
from api import modeling
app.include_router(modeling.router, prefix="/api/modeling", tags=["Modeling"])
```

- [ ] **Step 4: Run API and regression tests**

Run: `python -m pytest backend/tests/test_modeling_api.py backend/tests/test_agents_api.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the API**

```powershell
git add backend/api/modeling.py backend/main.py backend/tests/test_modeling_api.py
git commit -m "feat: expose modeling project API"
```

### Task 5: Frontend API, Navigation, and Project View

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/services/api.test.ts`
- Modify: `frontend/src/store/useStore.ts`
- Modify: `frontend/src/store/useStore.test.ts`
- Modify: `frontend/src/i18n.ts`
- Modify: `frontend/src/components/ModuleNav.tsx`
- Modify: `frontend/src/components/ModuleNav.test.tsx`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/views/ModelingProjectsView.tsx`
- Create: `frontend/src/views/ModelingProjectsView.test.tsx`

**Interfaces:**
- Consumes: Phase 1 REST endpoints.
- Produces: `ModelingProject`, `modelingApi`, the `modeling` app module, `selectedModelingProjectId`, and a project list/detail view.

- [ ] **Step 1: Add failing API and view tests**

Add this import and test to `frontend/src/services/api.test.ts`:

```typescript
import { modelingApi } from './api'

it('creates and lists modeling projects', async () => {
  httpClient.post.mockResolvedValue({ data: { project_id: 'p-1', name: 'Forecast', state: 'project_initialized' } })
  httpClient.get.mockResolvedValue({ data: { projects: [], total: 0 } })
  await modelingApi.create({ name: 'Forecast' })
  await modelingApi.list()
  expect(httpClient.post).toHaveBeenCalledWith('/modeling/projects', { name: 'Forecast' })
  expect(httpClient.get).toHaveBeenCalledWith('/modeling/projects')
})
```

Create `ModelingProjectsView.test.tsx`:

```typescript
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ModelingProjectsView from './ModelingProjectsView'

const list = vi.fn()
const create = vi.fn()
vi.mock('../services/api', () => ({ modelingApi: { list, create } }))

describe('ModelingProjectsView', () => {
  beforeEach(() => {
    list.mockResolvedValue({ projects: [{ project_id: 'p-1', name: 'Forecast', state: 'project_initialized' }], total: 1 })
    create.mockResolvedValue({ project_id: 'p-2', name: 'Churn', state: 'project_initialized' })
  })
  it('loads projects and creates a new one', async () => {
    render(<ModelingProjectsView />)
    expect(await screen.findByText('Forecast')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Project name'), { target: { value: 'Churn' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }))
    await waitFor(() => expect(create).toHaveBeenCalledWith({ name: 'Churn' }))
  })
})
```

- [ ] **Step 2: Run frontend tests and verify failure**

Run: `Set-Location frontend; npm test -- --run src/services/api.test.ts src/views/ModelingProjectsView.test.tsx`

Expected: FAIL because the API client and view are missing.

- [ ] **Step 3: Add frontend types and API methods**

```typescript
export interface ModelingProject {
  project_id: string
  name: string
  slug: string
  workspace_path: string
  state: string
  deadline?: string | null
  created_at?: string
  updated_at?: string
}

export const modelingApi = {
  list: async (): Promise<{ projects: ModelingProject[]; total: number }> => (await api.get('/modeling/projects')).data,
  create: async (data: { name: string; deadline?: string }): Promise<ModelingProject> => (await api.post('/modeling/projects', data)).data,
  get: async (projectId: string): Promise<ModelingProject> => (await api.get(`/modeling/projects/${projectId}`)).data,
  advance: async (projectId: string): Promise<ModelingProject> => (await api.post(`/modeling/projects/${projectId}/advance`)).data,
  rollback: async (projectId: string, reason: string): Promise<ModelingProject> => (await api.post(`/modeling/projects/${projectId}/rollback`, { reason })).data,
}
```

Extend `AppModule` with `'modeling'`, add `selectedModelingProjectId: string | null` and `setSelectedModelingProjectId`, persist it as `selected_modeling_project_id`, add `nav.modeling` and module title/subtitle translations, add a `Workflow` icon entry in `ModuleNav`, and render `ModelingProjectsView` from `App.tsx` when `activeModule === 'modeling'`.

- [ ] **Step 4: Implement the minimal project view**

```typescript
import { FormEvent, useEffect, useState } from 'react'
import { modelingApi, type ModelingProject } from '../services/api'

export default function ModelingProjectsView() {
  const [projects, setProjects] = useState<ModelingProject[]>([])
  const [name, setName] = useState('')
  const load = async () => setProjects((await modelingApi.list()).projects)
  useEffect(() => { void load() }, [])
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const created = await modelingApi.create({ name: name.trim() })
    setProjects((current) => [created, ...current])
    setName('')
  }
  return <div className="h-full overflow-y-auto p-6">
    <h2 className="text-xl font-semibold">Modeling projects</h2>
    <form onSubmit={submit} className="mt-4 flex gap-2">
      <label className="sr-only" htmlFor="project-name">Project name</label>
      <input id="project-name" aria-label="Project name" value={name} onChange={(event) => setName(event.target.value)} className="rounded border px-3 py-2" />
      <button disabled={!name.trim()} className="rounded bg-blue-600 px-3 py-2 text-white">Create project</button>
    </form>
    <ul className="mt-6 space-y-3">{projects.map((project) => <li key={project.project_id} className="rounded border p-4"><strong>{project.name}</strong><p>{project.state}</p></li>)}</ul>
  </div>
}
```

- [ ] **Step 5: Run frontend tests and production build**

Run: `Set-Location frontend; npm test -- --run src/services/api.test.ts src/views/ModelingProjectsView.test.tsx src/components/ModuleNav.test.tsx src/store/useStore.test.ts`

Expected: PASS.

Run: `Set-Location frontend; npm run build`

Expected: TypeScript and Vite build succeed.

- [ ] **Step 6: Commit the Phase 1 frontend**

```powershell
git add frontend/src/services/api.ts frontend/src/services/api.test.ts frontend/src/store/useStore.ts frontend/src/store/useStore.test.ts frontend/src/i18n.ts frontend/src/components/ModuleNav.tsx frontend/src/components/ModuleNav.test.tsx frontend/src/App.tsx frontend/src/views/ModelingProjectsView.tsx frontend/src/views/ModelingProjectsView.test.tsx
git commit -m "feat: add modeling project workbench entry"
```

### Task 6: Phase 1 Vertical Verification

**Files:**
- Modify only files required by failures found in this task.

**Interfaces:**
- Verifies every interface produced by Tasks 1–5.
- Produces: a green Phase 1 checkpoint commit if verification fixes are necessary.

- [ ] **Step 1: Run all modeling backend tests**

Run: `python -m pytest backend/tests/test_modeling_state.py backend/tests/test_modeling_store.py backend/tests/test_modeling_workspace.py backend/tests/test_modeling_project_service.py backend/tests/test_modeling_api.py -q`

Expected: PASS.

- [ ] **Step 2: Run the entire backend suite**

Run: `python -m pytest backend/tests -q`

Expected: all tests pass.

- [ ] **Step 3: Run the entire frontend suite and build**

Run: `Set-Location frontend; npm test -- --run`

Expected: all tests pass.

Run: `Set-Location frontend; npm run build`

Expected: production build succeeds.

- [ ] **Step 4: Manually verify persistence**

Start the app, create `Sales Forecast`, advance it once, stop both processes, restart, and reopen Modeling Projects.

Expected: the project remains visible in `problem_parsing`, and its workspace contains `.git`, `problem/original`, `data/raw`, `experiments`, `paper`, `deliverables`, and `.workflow/runs`.

- [ ] **Step 5: Confirm the checkpoint is clean**

Run: `git status --short`

Expected: no uncommitted Phase 1 files. If verification required a fix, return to the task that owns that file, repeat its focused tests, and use that task's explicit `git add` and `git commit` command before completing this checkpoint.
