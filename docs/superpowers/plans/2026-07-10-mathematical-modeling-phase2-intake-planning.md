# Mathematical Modeling Phase 2 Intake and Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import immutable competition inputs, profile real CSV data, generate structured problem and model-plan artifacts, and enforce a content-hashed model approval gate.

**Architecture:** Add artifact and approval services over the Phase 1 modeling database and filesystem workspace. Dedicated intake, profiling, and role services create versioned files; workflow gates inspect registered artifacts and approvals before allowing advancement.

**Tech Stack:** Python 3.10+, FastAPI multipart uploads, Pydantic 2.5, SQLite, hashlib, pathlib, PyPDF2 3.0.1, pandas 2.2.2, existing LLM service, React, TypeScript, Vitest.

## Global Constraints

- Follow the roadmap global constraints and complete Phase 1 first.
- Accept problem inputs as `.pdf`, `.md`, or `.txt`; accept MVP datasets as `.csv` only.
- Copy imports into `problem/original` or `data/raw`, preserve the original filename, and record SHA-256 before any analysis.
- Reject duplicate destination names, project-external paths, unsupported suffixes, and files larger than `MAX_FILE_SIZE`.
- Model planning returns at most three candidates and cannot claim experimental results.
- `model_approval` decisions bind the SHA-256 of the canonical approval payload.

---

## File Map

- Modify `backend/requirements.txt`: add `pandas==2.2.2`.
- Create `backend/services/modeling_contracts.py`: Pydantic artifact contracts.
- Create `backend/services/artifact_service.py`: artifact registration and resolution.
- Create `backend/services/approval_service.py`: request, decision, and hash validation.
- Modify `backend/services/modeling_store.py`: artifact and approval tables/methods.
- Create `backend/services/modeling_input_service.py`: immutable imports and manifests.
- Create `backend/services/data_profile_service.py`: deterministic CSV report.
- Create `backend/services/modeling_role_service.py`: structured problem/model LLM calls.
- Create `backend/services/modeling_agent_run_service.py`: shared task/run lifecycle for all modeling roles.
- Create `backend/services/modeling_gate_service.py`: Phase 2 exit checks.
- Modify `backend/services/modeling_project_service.py`: delegate advancement to gates.
- Modify `backend/api/modeling.py`: upload, artifact, planning, and approval endpoints.
- Create `backend/skills/modeling_problem_parser/skill.json`.
- Create `backend/skills/modeling_planner/skill.json`.
- Create focused backend tests for each service and API behavior.
- Modify `frontend/src/services/api.ts` and `frontend/src/services/api.test.ts`.
- Create `frontend/src/components/ModelingInputPanel.tsx` and test.
- Create `frontend/src/components/ModelPlanApprovalCard.tsx` and test.
- Modify `frontend/src/views/ModelingProjectsView.tsx` and its test.

### Task 1: Artifact and Approval Persistence

**Files:**
- Create: `backend/services/modeling_contracts.py`
- Create: `backend/services/artifact_service.py`
- Create: `backend/services/approval_service.py`
- Modify: `backend/services/modeling_store.py`
- Test: `backend/tests/test_artifact_service.py`
- Test: `backend/tests/test_approval_service.py`

**Interfaces:**
- Produces: `ArtifactService.register/resolve/list_for_project` and `ApprovalService.request/decide/require_approved` exactly as declared in the roadmap.
- Consumes: a project dictionary containing `workspace_path` and the Phase 1 `ModelingStore` connection pattern.

- [ ] **Step 1: Write failing artifact and approval tests**

```python
import json


def test_artifact_registers_hash_and_rejects_escape(tmp_path, modeling_store, project):
    target = tmp_path / "analysis" / "model_plan.md"
    target.parent.mkdir()
    target.write_text("plan", encoding="utf-8")
    service = ArtifactService(modeling_store)
    artifact = service.register(project["project_id"], "model_plan", "analysis/model_plan.md")
    assert artifact["sha256"] == hashlib.sha256(b"plan").hexdigest()
    with pytest.raises(ValueError, match="outside project workspace"):
        service.register(project["project_id"], "model_plan", "../secret.txt")


def test_changed_payload_invalidates_approval(modeling_store, project):
    service = ApprovalService(modeling_store)
    request = service.request(project["project_id"], "model_approval", {"artifact_id": "a-1", "version": 1})
    approved = service.decide(request["approval_id"], "approved", request["payload_hash"], "Looks correct")
    assert approved["decision"] == "approved"
    service.require_approved(project["project_id"], "model_approval", request["payload_hash"])
    with pytest.raises(ValueError, match="approval does not match"):
        service.require_approved(project["project_id"], "model_approval", hashlib.sha256(b"changed").hexdigest())
```

- [ ] **Step 2: Run tests and verify missing services**

Run: `python -m pytest backend/tests/test_artifact_service.py backend/tests/test_approval_service.py -q`

Expected: FAIL on missing imports.

- [ ] **Step 3: Extend the store with artifact and approval tables**

Add these tables inside `ModelingStore._init_db`:

```python
conn.execute("CREATE TABLE IF NOT EXISTS project_artifacts (artifact_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, artifact_type TEXT NOT NULL, relative_path TEXT NOT NULL, sha256 TEXT NOT NULL, source_run_id TEXT, source_experiment_id TEXT, version INTEGER NOT NULL, created_at TEXT NOT NULL, UNIQUE(project_id, relative_path, version))")
conn.execute("CREATE TABLE IF NOT EXISTS approval_requests (approval_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, gate TEXT NOT NULL, payload_json TEXT NOT NULL, payload_hash TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
conn.execute("CREATE TABLE IF NOT EXISTS approval_decisions (decision_id TEXT PRIMARY KEY, approval_id TEXT NOT NULL, decision TEXT NOT NULL, payload_hash TEXT NOT NULL, comment TEXT NOT NULL, created_at TEXT NOT NULL)")
```

Add explicit insert/select methods named `create_artifact`, `list_artifacts`, `get_artifact`, `create_approval_request`, `get_approval_request`, `create_approval_decision`, and `find_approved_request`. Each method returns `dict(row)`. Serialize approval payloads with `json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))` before insertion and deserialize them back to `payload` on reads.

- [ ] **Step 4: Implement canonical hashing and safe artifact paths**

```python
import hashlib
import json
from pathlib import Path


def canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ArtifactService:
    def __init__(self, store):
        self.store = store

    def register(self, project_id: str, artifact_type: str, relative_path: str, source_run_id: str | None = None, source_experiment_id: str | None = None) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        root = Path(project["workspace_path"]).resolve()
        target = (root / relative_path).resolve()
        if target == root or root not in target.parents:
            raise ValueError("Artifact path is outside project workspace")
        if not target.is_file():
            raise ValueError("Artifact file does not exist")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        version = 1 + len([item for item in self.store.list_artifacts(project_id) if item["relative_path"] == relative_path])
        return self.store.create_artifact(project_id, artifact_type, relative_path.replace("\\", "/"), digest, source_run_id, source_experiment_id, version)

    def resolve(self, project_id: str, artifact_id: str) -> dict:
        artifact = self.store.get_artifact(artifact_id)
        if not artifact or artifact["project_id"] != project_id:
            raise ValueError("Artifact not found")
        return artifact

    def list_for_project(self, project_id: str) -> list[dict]:
        return self.store.list_artifacts(project_id)
```

- [ ] **Step 5: Implement approval decisions**

```python
class ApprovalService:
    def __init__(self, store):
        self.store = store

    def request(self, project_id: str, gate: str, payload: dict) -> dict:
        return self.store.create_approval_request(project_id, gate, payload, canonical_hash(payload))

    def decide(self, approval_id: str, decision: str, payload_hash: str, comment: str = "") -> dict:
        if decision not in {"approved", "changes_requested", "rejected"}:
            raise ValueError("Invalid approval decision")
        request = self.store.get_approval_request(approval_id)
        if not request or request["payload_hash"] != payload_hash:
            raise ValueError("Approval payload has changed")
        return self.store.create_approval_decision(approval_id, decision, payload_hash, comment)

    def require_approved(self, project_id: str, gate: str, payload_hash: str) -> dict:
        decision = self.store.find_approved_request(project_id, gate, payload_hash)
        if not decision:
            raise ValueError("Required approval does not match current content")
        return decision
```

- [ ] **Step 6: Run tests and commit**

Run: `python -m pytest backend/tests/test_artifact_service.py backend/tests/test_approval_service.py -q`

Expected: PASS.

```powershell
git add backend/services/modeling_contracts.py backend/services/modeling_store.py backend/services/artifact_service.py backend/services/approval_service.py backend/tests/test_artifact_service.py backend/tests/test_approval_service.py
git commit -m "feat: add modeling artifacts and approval records"
```

### Task 2: Immutable Input Import and Manifests

**Files:**
- Create: `backend/services/modeling_input_service.py`
- Test: `backend/tests/test_modeling_input_service.py`

**Interfaces:**
- Consumes: `ArtifactService.register` and project workspace paths.
- Produces: `import_input(project_id: str, filename: str, content: bytes, kind: str) -> dict` and `data/data_manifest.json`.

- [ ] **Step 1: Write failing import tests**

```python
def test_imports_csv_without_mutating_source(tmp_path, input_service, project):
    result = input_service.import_input(project["project_id"], "train.csv", b"x,y\n1,2\n", "data")
    target = tmp_path / "data" / "raw" / "train.csv"
    assert target.read_bytes() == b"x,y\n1,2\n"
    assert result["relative_path"] == "data/raw/train.csv"
    manifest = json.loads((tmp_path / "data" / "data_manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"][0]["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()


def test_rejects_unsupported_and_duplicate_names(input_service, project):
    with pytest.raises(ValueError, match="Unsupported data file"):
        input_service.import_input(project["project_id"], "payload.py", b"print(1)", "data")
    input_service.import_input(project["project_id"], "train.csv", b"x\n1\n", "data")
    with pytest.raises(ValueError, match="already exists"):
        input_service.import_input(project["project_id"], "train.csv", b"x\n2\n", "data")
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest backend/tests/test_modeling_input_service.py -q`

Expected: FAIL because the input service is missing.

- [ ] **Step 3: Implement filename, size, suffix, and manifest rules**

```python
import hashlib
import json
from pathlib import Path, PurePath


class ModelingInputService:
    PROBLEM_SUFFIXES = {".pdf", ".md", ".txt"}
    DATA_SUFFIXES = {".csv"}

    def __init__(self, store, artifact_service, max_file_size: int):
        self.store = store
        self.artifact_service = artifact_service
        self.max_file_size = max_file_size

    def import_input(self, project_id: str, filename: str, content: bytes, kind: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        clean = PurePath(filename).name
        if clean != filename or not clean:
            raise ValueError("Invalid input filename")
        suffixes = self.PROBLEM_SUFFIXES if kind == "problem" else self.DATA_SUFFIXES if kind == "data" else set()
        if Path(clean).suffix.lower() not in suffixes:
            raise ValueError(f"Unsupported {kind} file")
        if len(content) > self.max_file_size:
            raise ValueError("Input file exceeds size limit")
        relative = Path("problem/original" if kind == "problem" else "data/raw") / clean
        target = Path(project["workspace_path"]) / relative
        if target.exists():
            raise ValueError("Input file already exists")
        target.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        manifest_path = Path(project["workspace_path"]) / ("problem/input_manifest.json" if kind == "problem" else "data/data_manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"files": []}
        manifest["files"].append({"filename": clean, "relative_path": relative.as_posix(), "sha256": digest, "size": len(content)})
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        target.chmod(0o444)
        return self.artifact_service.register(project_id, f"{kind}_input", relative.as_posix())
```

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest backend/tests/test_modeling_input_service.py -q`

Expected: PASS.

```powershell
git add backend/services/modeling_input_service.py backend/tests/test_modeling_input_service.py
git commit -m "feat: import immutable modeling inputs"
```

### Task 3: Deterministic CSV Profiling

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/services/data_profile_service.py`
- Test: `backend/tests/test_data_profile_service.py`

**Interfaces:**
- Consumes: registered `data_input` artifact and project workspace.
- Produces: `profile(project_id: str, artifact_id: str) -> dict`, `analysis/data_profile.json`, and `analysis/data_report.md`.

- [ ] **Step 1: Add pandas and install dependencies**

Add one exact line to `backend/requirements.txt`:

```text
pandas==2.2.2
```

Run: `python -m pip install -r backend/requirements.txt`

Expected: pandas 2.2.2 installs successfully.

- [ ] **Step 2: Write a failing profile test**

```python
def test_profiles_types_missing_duplicates_and_numeric_summary(tmp_path, profile_service, project, data_artifact):
    result = profile_service.profile(project["project_id"], data_artifact["artifact_id"])
    assert result["row_count"] == 3
    assert result["column_count"] == 2
    assert result["duplicate_rows"] == 1
    assert result["columns"]["target"]["missing"] == 1
    assert (tmp_path / "analysis" / "data_report.md").is_file()
```

- [ ] **Step 3: Run and verify failure**

Run: `python -m pytest backend/tests/test_data_profile_service.py -q`

Expected: FAIL because `DataProfileService` is missing.

- [ ] **Step 4: Implement stable JSON-safe profiling**

```python
import json
from pathlib import Path
import pandas as pd


class DataProfileService:
    def __init__(self, store, artifact_service):
        self.store = store
        self.artifact_service = artifact_service

    def profile(self, project_id: str, artifact_id: str) -> dict:
        project = self.store.get_project(project_id)
        artifact = self.artifact_service.resolve(project_id, artifact_id)
        source = Path(project["workspace_path"]) / artifact["relative_path"]
        frame = pd.read_csv(source)
        columns = {}
        for name in frame.columns:
            series = frame[name]
            item = {"dtype": str(series.dtype), "missing": int(series.isna().sum()), "unique": int(series.nunique(dropna=True))}
            if pd.api.types.is_numeric_dtype(series) and not series.dropna().empty:
                clean = series.dropna()
                item["numeric"] = {"min": float(clean.min()), "max": float(clean.max()), "mean": float(clean.mean()), "std": float(clean.std(ddof=0))}
            columns[str(name)] = item
        result = {"source_artifact_id": artifact_id, "row_count": int(len(frame)), "column_count": int(len(frame.columns)), "duplicate_rows": int(frame.duplicated().sum()), "columns": columns}
        analysis = Path(project["workspace_path"]) / "analysis"
        (analysis / "data_profile.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        lines = ["# Data Profile", "", f"Rows: {result['row_count']}", f"Columns: {result['column_count']}", f"Duplicate rows: {result['duplicate_rows']}"]
        (analysis / "data_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.artifact_service.register(project_id, "data_profile", "analysis/data_profile.json")
        self.artifact_service.register(project_id, "data_report", "analysis/data_report.md")
        return result
```

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest backend/tests/test_data_profile_service.py -q`

Expected: PASS.

```powershell
git add backend/requirements.txt backend/services/data_profile_service.py backend/tests/test_data_profile_service.py
git commit -m "feat: profile modeling CSV inputs"
```

### Task 4: Structured Problem and Model-Plan Agents

**Files:**
- Create: `backend/services/modeling_role_service.py`
- Create: `backend/services/modeling_agent_run_service.py`
- Create: `backend/services/modeling_gate_service.py`
- Modify: `backend/services/modeling_project_service.py`
- Create: `backend/skills/modeling_problem_parser/skill.json`
- Create: `backend/skills/modeling_planner/skill.json`
- Test: `backend/tests/test_modeling_role_service.py`
- Test: `backend/tests/test_modeling_agent_run_service.py`
- Test: `backend/tests/test_modeling_gate_service.py`

**Interfaces:**
- Consumes: `LLMService.generate`, profile artifacts, `ArtifactService`, and `ApprovalService`.
- Produces: `parse_problem`, `create_model_plan`, and Phase 2 workflow exit checks.

- [ ] **Step 1: Write failing structured-output tests**

```python
def test_model_plan_rejects_more_than_three_candidates(tmp_path, role_service, project):
    role_service.llm.generate = AsyncMock(return_value=json.dumps({"problem_summary": "Forecast", "candidates": [{"name": str(index), "assumptions": [], "features": [], "algorithm": "linear", "metrics": ["rmse"], "risks": []} for index in range(4)]}))
    with pytest.raises(ValueError, match="at most 3"):
        asyncio.run(role_service.create_model_plan(project["project_id"], "analysis/data_profile.json"))


def test_gate_requires_matching_model_approval(gate_service, project, model_artifact):
    with pytest.raises(ValueError, match="model approval"):
        gate_service.require_exit(project["project_id"], "model_approval_pending")
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest backend/tests/test_modeling_role_service.py backend/tests/test_modeling_agent_run_service.py backend/tests/test_modeling_gate_service.py -q`

Expected: FAIL on missing services.

- [ ] **Step 3: Define Pydantic contracts and implement strict JSON extraction**

```python
import json
from pydantic import BaseModel, Field


class ModelCandidate(BaseModel):
    name: str
    assumptions: list[str]
    features: list[str]
    algorithm: str
    metrics: list[str]
    risks: list[str]


class ModelPlan(BaseModel):
    problem_summary: str
    candidates: list[ModelCandidate] = Field(min_length=1, max_length=3)


def parse_json_object(text: str) -> dict:
    clean = text.strip()
    if clean.startswith("```json") and clean.endswith("```"):
        clean = clean[7:-3].strip()
    value = json.loads(clean)
    if not isinstance(value, dict):
        raise ValueError("Agent output must be a JSON object")
    return value
```

`ModelingRoleService.create_model_plan` reads `problem/problem_spec.json` and `analysis/data_profile.json`, asks the LLM for JSON matching `ModelPlan.model_json_schema()`, validates with `ModelPlan.model_validate`, writes both `analysis/model_plan.json` and a deterministic `analysis/model_plan.md`, then registers both artifacts. `parse_problem` follows the same pattern with fields `title`, `subproblems`, `objectives`, `constraints`, `evaluation_requirements`, and `deliverables`.

Both methods create inspectable tasks and Agent runs through a reusable lifecycle service that later programmer, paper, and reviewer roles also consume:

```python
class ModelingAgentRunService:
    def __init__(self, modeling_store, agent_store):
        self.modeling_store = modeling_store
        self.agent_store = agent_store

    def start(self, project_id: str, stage: str, role: str, skill_id: str, inputs: dict, required_outputs: list[str]) -> tuple[dict, dict]:
        task = self.modeling_store.create_task(project_id, stage, role, inputs, required_outputs)
        self.modeling_store.update_task(task["task_id"], "running", 0)
        run = self.agent_store.create_agent_run(skill_id, inputs, project_id=project_id, task_id=task["task_id"], stage=stage)
        return task, run

    def complete(self, task_id: str, run_id: str, artifact_ids: list[str]) -> None:
        self.agent_store.append_agent_step(run_id, {"kind": "artifacts", "title": "Registered modeling artifacts", "payload": {"artifact_ids": artifact_ids}})
        self.agent_store.update_agent_run_status(run_id, "completed")
        self.modeling_store.update_task(task_id, "completed", 0)

    def fail(self, task: dict, run_id: str, safe_error: str) -> None:
        retries = task["retry_count"] + 1
        self.agent_store.append_agent_step(run_id, {"kind": "error", "title": "Modeling role failed", "payload": {"error": safe_error}})
        self.agent_store.update_agent_run_status(run_id, "failed", error=safe_error)
        self.modeling_store.update_task(task["task_id"], "blocked" if retries >= 3 else "failed", retries)
```

On success, the role calls `complete` and returns task/run IDs with the artifacts. On validation or LLM failure it sanitizes the error and calls `fail`; the third failed attempt blocks the task.

- [ ] **Step 4: Implement gate checks and wire project advancement**

```python
class ModelingGateService:
    def __init__(self, store, approval_service):
        self.store = store
        self.approval_service = approval_service

    def require_exit(self, project_id: str, state: str) -> None:
        artifacts = self.store.list_artifacts(project_id)
        kinds = {item["artifact_type"] for item in artifacts}
        required = {
            "problem_parsing": {"problem_spec"},
            "data_profiling": {"data_profile", "data_report"},
            "model_planning": {"model_plan"},
        }
        missing = required.get(state, set()) - kinds
        if missing:
            raise ValueError("Missing required artifacts: " + ", ".join(sorted(missing)))
        if state == "model_approval_pending":
            plan = max((item for item in artifacts if item["artifact_type"] == "model_plan"), key=lambda item: item["version"])
            payload = {"artifact_id": plan["artifact_id"], "artifact_sha256": plan["sha256"], "version": plan["version"]}
            self.approval_service.require_approved(project_id, "model_approval", canonical_hash(payload))
```

Call `self.gate_service.require_exit(project_id, project["state"])` immediately before `next_state` in `ModelingProjectService.advance`.

- [ ] **Step 5: Add role manifests**

`modeling_problem_parser/skill.json`:

```json
{"skill_id":"modeling_problem_parser","name":"Modeling Problem Parser","description":"Extract structured requirements from a modeling competition prompt.","allowed_tools":["retrieve_sources","create_output"],"prompt_template":"Return only JSON matching the supplied problem specification schema. Do not invent competition requirements.","output_kind":"problem_spec"}
```

`modeling_planner/skill.json`:

```json
{"skill_id":"modeling_planner","name":"Modeling Planner","description":"Propose up to three data-driven modeling candidates from approved inputs.","allowed_tools":["retrieve_sources","create_output"],"prompt_template":"Return only JSON matching the supplied model plan schema. Describe expected evaluation but never claim unrun results.","output_kind":"model_plan"}
```

- [ ] **Step 6: Run tests and commit**

Run: `python -m pytest backend/tests/test_modeling_role_service.py backend/tests/test_modeling_gate_service.py backend/tests/test_skill_service.py -q`

Expected: PASS.

```powershell
git add backend/services/modeling_role_service.py backend/services/modeling_agent_run_service.py backend/services/modeling_gate_service.py backend/services/modeling_project_service.py backend/skills/modeling_problem_parser/skill.json backend/skills/modeling_planner/skill.json backend/tests/test_modeling_role_service.py backend/tests/test_modeling_agent_run_service.py backend/tests/test_modeling_gate_service.py
git commit -m "feat: generate and approve modeling plans"
```

### Task 5: Phase 2 API and Approval UI

**Files:**
- Modify: `backend/api/modeling.py`
- Test: `backend/tests/test_modeling_intake_api.py`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/services/api.test.ts`
- Create: `frontend/src/components/ModelingInputPanel.tsx`
- Create: `frontend/src/components/ModelingInputPanel.test.tsx`
- Create: `frontend/src/components/ModelPlanApprovalCard.tsx`
- Create: `frontend/src/components/ModelPlanApprovalCard.test.tsx`
- Modify: `frontend/src/views/ModelingProjectsView.tsx`
- Modify: `frontend/src/views/ModelingProjectsView.test.tsx`

**Interfaces:**
- Produces: multipart input upload, profile/parse/plan actions, artifact listing, approval listing, and approval decision UI.
- Consumes: all Phase 2 services.

- [ ] **Step 1: Add failing backend API tests**

```python
def test_upload_rejects_unknown_kind():
    request = modeling.InputUploadKind(kind="executable")
    with pytest.raises(HTTPException) as raised:
        asyncio.run(modeling.validate_input_kind(request))
    assert raised.value.status_code == 400


def test_approval_decision_passes_payload_hash(fake_services):
    response = asyncio.run(modeling.decide_approval("p-1", "a-1", modeling.ApprovalDecision(decision="approved", payload_hash="abc", comment="ok")))
    assert response["decision"] == "approved"
```

- [ ] **Step 2: Add endpoints and frontend client methods**

Backend routes:

```text
POST /projects/{project_id}/inputs?kind=problem|data
POST /projects/{project_id}/problem/parse
POST /projects/{project_id}/data/profile/{artifact_id}
POST /projects/{project_id}/model-plan
GET  /projects/{project_id}/artifacts
GET  /projects/{project_id}/artifacts/{artifact_id}
GET  /projects/{project_id}/approvals
POST /projects/{project_id}/approvals/{approval_id}/decide
```

Each route resolves the project from the service, returns 404 for missing project/artifact, 400 for invalid input, and 409 for an invalid state or stale approval hash. The frontend `modelingApi` gains matching methods with typed `ModelingArtifact` and `ApprovalRequest` responses.

- [ ] **Step 3: Implement upload and approval components**

`ModelingInputPanel` has separate problem/data file inputs and calls `modelingApi.uploadInput(projectId, kind, file)`. `ModelPlanApprovalCard` renders the plan artifact hash, candidates and risks, requires a non-empty modification comment for `changes_requested`, and sends the exact `payload_hash` returned by the API.

Use this decision call:

```typescript
await modelingApi.decideApproval(projectId, approval.approval_id, {
  decision,
  payload_hash: approval.payload_hash,
  comment: comment.trim(),
})
```

- [ ] **Step 4: Run Phase 2 focused tests**

Run: `python -m pytest backend/tests/test_modeling_intake_api.py backend/tests/test_modeling_input_service.py backend/tests/test_data_profile_service.py backend/tests/test_modeling_role_service.py backend/tests/test_modeling_gate_service.py -q`

Expected: PASS.

Run: `Set-Location frontend; npm test -- --run src/services/api.test.ts src/components/ModelingInputPanel.test.tsx src/components/ModelPlanApprovalCard.test.tsx src/views/ModelingProjectsView.test.tsx`

Expected: PASS.

- [ ] **Step 5: Run full suites and build**

Run: `python -m pytest backend/tests -q`

Expected: all backend tests pass.

Run: `Set-Location frontend; npm test -- --run; npm run build`

Expected: all frontend tests and the production build pass.

- [ ] **Step 6: Commit API and UI**

```powershell
git add backend/api/modeling.py backend/tests/test_modeling_intake_api.py frontend/src/services/api.ts frontend/src/services/api.test.ts frontend/src/components/ModelingInputPanel.tsx frontend/src/components/ModelingInputPanel.test.tsx frontend/src/components/ModelPlanApprovalCard.tsx frontend/src/components/ModelPlanApprovalCard.test.tsx frontend/src/views/ModelingProjectsView.tsx frontend/src/views/ModelingProjectsView.test.tsx
git commit -m "feat: add modeling intake and plan approval UI"
```

### Task 6: Phase 2 Real-Data Checkpoint

**Files:**
- No source changes expected.

**Interfaces:**
- Verifies the complete Phase 2 vertical slice.

- [ ] **Step 1: Create a project and upload a prompt plus CSV through the UI**

Use a UTF-8 text prompt and a CSV with one numeric target, one categorical feature, one missing value, and one duplicate row.

Expected: both files appear below their immutable raw directories with matching manifest hashes.

- [ ] **Step 2: Run parsing, profiling, and planning**

Expected: `problem_spec.json`, `data_profile.json`, `data_report.md`, `model_plan.json`, and `model_plan.md` exist and are registered.

- [ ] **Step 3: Approve the model plan and then modify its file on disk**

Expected: the original hash is approved; after modification, advancement fails with HTTP 409 because approval no longer matches.

- [ ] **Step 4: Restore the registered plan and confirm a clean repository checkpoint**

Run: `git status --short`

Expected: no uncommitted Phase 2 application files.
