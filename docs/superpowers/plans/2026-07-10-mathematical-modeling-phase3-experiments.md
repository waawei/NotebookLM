# Mathematical Modeling Phase 3 Experiments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate reviewable Python experiments, bind execution approval to exact code and commands, run inside a restricted project boundary, and persist immutable metrics, figures, logs, and environment evidence.

**Architecture:** A code-agent service writes only declared project files. An execution-policy service canonicalizes the batch payload and requests approval; a subprocess runner accepts only validated argument arrays and emits an immutable experiment directory registered through the artifact service.

**Tech Stack:** Python 3.10+, Pydantic, subprocess, pathlib, hashlib, psutil 6.0.0, pandas 2.2.2, NumPy 1.26.4, scikit-learn 1.4.2, matplotlib 3.8.4, pytest 8.2.2, React, TypeScript, Vitest.

## Global Constraints

- Complete Phases 1 and 2 first and follow the roadmap constraints.
- Every experiment has an ID `exp-NNNN`; an existing experiment directory is never modified.
- Commands are JSON arrays beginning with the project virtual-environment Python executable; shell strings are rejected.
- Network is denied by a generated `sitecustomize.py` unless the execution approval payload explicitly records and visibly highlights `network_allowed: true`.
- Code, command, dependency lock, input artifact hashes, timeout, and output limit are part of the execution approval hash.
- The runner scrubs key/token/password/authorization environment variables and kills the full child process tree on timeout.

---

## File Map

- Modify `backend/requirements.txt`: add exact numerical/runtime dependencies.
- Create `backend/services/experiment_contracts.py`.
- Create `backend/services/execution_policy.py`.
- Create `backend/services/project_environment_service.py`.
- Create `backend/services/restricted_runner.py`.
- Create `backend/services/experiment_service.py`.
- Create `backend/services/modeling_code_agent_service.py`.
- Create `backend/services/environment_capture.py`.
- Modify `backend/services/modeling_store.py`: experiment records.
- Modify `backend/services/modeling_gate_service.py`: execution and result gates.
- Modify `backend/api/modeling.py`: experiment endpoints.
- Create `backend/skills/modeling_programmer/skill.json`.
- Create backend tests for contracts, policy, runner, service, gate, and API.
- Modify `frontend/src/services/api.ts` and tests.
- Create `frontend/src/components/ExperimentApprovalCard.tsx` and test.
- Create `frontend/src/components/ExperimentRunPanel.tsx` and test.
- Modify `frontend/src/views/ModelingProjectsView.tsx` and test.

### Task 1: Experiment Contracts and Records

**Files:**
- Create: `backend/services/experiment_contracts.py`
- Modify: `backend/services/modeling_store.py`
- Test: `backend/tests/test_experiment_contracts.py`
- Test: `backend/tests/test_experiment_store.py`

**Interfaces:**
- Produces: `ExperimentConfig`, `ExecutionBatch`, `MetricRecord`, `create_experiment`, `update_experiment_status`, `get_experiment`, and `list_experiments`.
- Consumes: Phase 2 project and artifact IDs.

- [ ] **Step 1: Write failing contract tests**

```python
import pytest
from pydantic import ValidationError
from services.experiment_contracts import ExecutionBatch, ExperimentConfig


def test_batch_rejects_shell_string_and_invalid_experiment_id():
    with pytest.raises(ValidationError):
        ExecutionBatch(experiment_id="experiment-one", commands=["python train.py"], timeout_seconds=60, max_output_bytes=1000, network_allowed=False)


def test_config_requires_seed_and_declared_metric_direction():
    config = ExperimentConfig(experiment_id="exp-0001", seed=42, target="sales", features=["price"], model={"kind": "linear_regression", "parameters": {}}, metrics=[{"name": "rmse", "direction": "minimize"}])
    assert config.seed == 42
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest backend/tests/test_experiment_contracts.py backend/tests/test_experiment_store.py -q`

Expected: FAIL because contracts and experiment persistence do not exist.

- [ ] **Step 3: Implement strict Pydantic contracts**

```python
from typing import Literal
from pydantic import BaseModel, Field


class MetricSpec(BaseModel):
    name: str
    direction: Literal["minimize", "maximize"]


class ModelSpec(BaseModel):
    kind: str
    parameters: dict[str, str | int | float | bool]


class ExperimentConfig(BaseModel):
    experiment_id: str = Field(pattern=r"^exp-[0-9]{4}$")
    seed: int
    target: str
    features: list[str] = Field(min_length=1)
    model: ModelSpec
    metrics: list[MetricSpec] = Field(min_length=1)


class ExecutionBatch(BaseModel):
    experiment_id: str = Field(pattern=r"^exp-[0-9]{4}$")
    commands: list[list[str]] = Field(min_length=1)
    timeout_seconds: int = Field(ge=1, le=3600)
    max_output_bytes: int = Field(ge=1024, le=10_485_760)
    network_allowed: bool = False
    code_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_hashes: dict[str, str]


class MetricRecord(BaseModel):
    name: str
    value: float
    split: Literal["train", "validation", "test"]
```

- [ ] **Step 4: Add immutable experiment persistence**

Add to `_init_db`:

```python
conn.execute("CREATE TABLE IF NOT EXISTS experiment_runs (experiment_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, config_json TEXT NOT NULL, execution_payload_hash TEXT, status TEXT NOT NULL, pid INTEGER, exit_code INTEGER, error_code TEXT, started_at TEXT, finished_at TEXT, created_at TEXT NOT NULL)")
```

`create_experiment` must insert once and surface `sqlite3.IntegrityError` as `ValueError("Experiment already exists")`. `update_experiment_status` updates only status, process ID, exit code, error code, start, and finish fields; it never changes `config_json` or the experiment ID.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest backend/tests/test_experiment_contracts.py backend/tests/test_experiment_store.py -q`

Expected: PASS.

```powershell
git add backend/services/experiment_contracts.py backend/services/modeling_store.py backend/tests/test_experiment_contracts.py backend/tests/test_experiment_store.py
git commit -m "feat: add immutable experiment records"
```

### Task 2: Code Generation Contract and Project Template

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/services/modeling_code_agent_service.py`
- Create: `backend/skills/modeling_programmer/skill.json`
- Test: `backend/tests/test_modeling_code_agent_service.py`

**Interfaces:**
- Consumes: approved model-plan artifact, data-profile artifact, raw CSV artifact, `LLMService.generate`, and Phase 2 `ModelingAgentRunService`.
- Produces: `prepare_experiment(project_id: str, candidate_index: int) -> dict`, source files, tests, config, and an execution-batch draft.

- [ ] **Step 1: Add exact runtime dependencies**

Append to `backend/requirements.txt`:

```text
numpy==1.26.4
scikit-learn==1.4.2
matplotlib==3.8.4
psutil==6.0.0
pytest==8.2.2
```

Run: `python -m pip install -r backend/requirements.txt`

Expected: all pinned packages install.

- [ ] **Step 2: Write a failing path allowlist test**

```python
def test_code_agent_rejects_undeclared_file(role_service, project):
    role_service.llm.generate = AsyncMock(return_value=json.dumps({"files": [{"path": "../escape.py", "content": "print(1)"}], "commands": [["python", "../escape.py"]]}))
    with pytest.raises(ValueError, match="allowed source path"):
        asyncio.run(role_service.prepare_experiment(project["project_id"], 0))
```

- [ ] **Step 3: Implement a bounded generated-file schema**

```python
from pathlib import PurePosixPath
from pydantic import BaseModel, Field, field_validator


class GeneratedFile(BaseModel):
    path: str
    content: str = Field(max_length=200_000)

    @field_validator("path")
    @classmethod
    def allowed_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        allowed = {"src/prepare.py", "src/features.py", "src/train.py", "src/evaluate.py", "src/visualize.py", "tests/test_pipeline.py", "requirements.txt"}
        if path.as_posix() not in allowed:
            raise ValueError("Generated file is not an allowed source path")
        return path.as_posix()


class GeneratedExperiment(BaseModel):
    files: list[GeneratedFile] = Field(min_length=1)
    commands: list[list[str]] = Field(min_length=1)
```

`prepare_experiment` selects the next unused four-digit experiment ID, validates the LLM JSON, writes files only after every file validates, writes the matching `experiments/exp-0001/config.json`-style path, computes the combined source hash in sorted path order, and returns an unapproved `ExecutionBatch` payload. It must rebuild the current model-approval payload from artifact ID, artifact SHA-256, and version, then require its canonical hash to have an approved `model_approval` decision.

After validating commands, the service also writes deterministic project-level reproduction files instead of asking the LLM to invent them:

```python
reproduce = "\n".join([
    "$ErrorActionPreference = 'Stop'",
    "& .\\.venv\\Scripts\\python.exe -m pytest tests",
    "& .\\.venv\\Scripts\\python.exe src\\prepare.py --config experiments\\exp-0001\\config.json",
    "& .\\.venv\\Scripts\\python.exe src\\train.py --config experiments\\exp-0001\\config.json",
    "& .\\.venv\\Scripts\\python.exe src\\evaluate.py --experiment exp-0001",
]) + "\n"
(workspace / "reproduce.ps1").write_text(reproduce, encoding="utf-8")
readme = "# Modeling Project\n\nRun `powershell -ExecutionPolicy Bypass -File reproduce.ps1` from this directory.\n"
(workspace / "README.md").write_text(readme, encoding="utf-8")
```

When later experiments replace the selected final model, regenerate these two files with the selected experiment ID before packaging.

- [ ] **Step 4: Add the programmer manifest**

```json
{"skill_id":"modeling_programmer","name":"Modeling Programmer","description":"Implement an approved data-driven model as a reproducible Python experiment.","allowed_tools":["retrieve_sources","create_output"],"prompt_template":"Return only JSON matching the supplied generated-experiment schema. Use deterministic seeds, train-validation separation, machine-readable metrics, and project-relative paths.","output_kind":"experiment_source"}
```

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest backend/tests/test_modeling_code_agent_service.py backend/tests/test_skill_service.py -q`

Expected: PASS.

```powershell
git add backend/requirements.txt backend/services/modeling_code_agent_service.py backend/skills/modeling_programmer/skill.json backend/tests/test_modeling_code_agent_service.py
git commit -m "feat: generate bounded modeling experiments"
```

### Task 3: Execution Policy and Approval Ticket

**Files:**
- Create: `backend/services/execution_policy.py`
- Create: `backend/services/project_environment_service.py`
- Test: `backend/tests/test_execution_policy.py`
- Test: `backend/tests/test_project_environment_service.py`

**Interfaces:**
- Consumes: `ExecutionBatch`, project workspace, `ApprovalService`, and virtual-environment Python path.
- Produces: `validate_batch`, `request_execution`, and `require_execution_approval`.

- [ ] **Step 1: Write failing policy tests**

```python
def test_policy_rejects_shell_and_external_paths(policy, project, batch):
    bad = batch.model_copy(update={"commands": [["powershell", "-Command", "Remove-Item", "x"]]})
    with pytest.raises(ValueError, match="virtual environment Python"):
        policy.validate_batch(project, bad)


def test_changed_command_invalidates_execution_approval(policy, project, batch):
    request = policy.request_execution(project, batch)
    policy.approvals.decide(request["approval_id"], "approved", request["payload_hash"], "run")
    policy.require_execution_approval(project, batch)
    changed = batch.model_copy(update={"timeout_seconds": batch.timeout_seconds + 1})
    with pytest.raises(ValueError, match="approval"):
        policy.require_execution_approval(project, changed)
```

- [ ] **Step 2: Implement canonical command validation**

Create the project environment before validating its Python path:

```python
import subprocess
import sys
from pathlib import Path


class ProjectEnvironmentService:
    def ensure_created(self, project: dict) -> Path:
        root = Path(project["workspace_path"]).resolve()
        python_path = root / ".venv" / "Scripts" / "python.exe"
        if not python_path.is_file():
            subprocess.run([sys.executable, "-m", "venv", str(root / ".venv")], cwd=root, check=True, capture_output=True, text=True)
        return python_path.resolve()
```

The dependency-install command is part of the same content-hashed execution batch:

```python
[str(project_python), "-m", "pip", "install", "--requirement", "requirements.txt"]
```

It requires `network_allowed: true`; the UI highlights that network access applies to the entire batch. Subsequent offline experiment batches omit the install command and set `network_allowed: false`.

```python
from pathlib import Path
from services.approval_service import canonical_hash


class ExecutionPolicy:
    def __init__(self, approvals):
        self.approvals = approvals

    def validate_batch(self, project: dict, batch) -> None:
        root = Path(project["workspace_path"]).resolve()
        python_path = (root / ".venv" / "Scripts" / "python.exe").resolve()
        for command in batch.commands:
            if not command or Path(command[0]).resolve() != python_path:
                raise ValueError("Command must use the project virtual environment Python")
            for argument in command[1:]:
                if Path(argument).is_absolute():
                    resolved = Path(argument).resolve()
                    if resolved != root and root not in resolved.parents:
                        raise ValueError("Command path escapes project workspace")

    def request_execution(self, project: dict, batch) -> dict:
        self.validate_batch(project, batch)
        return self.approvals.request(project["project_id"], "execution_approval", batch.model_dump(mode="json"))

    def require_execution_approval(self, project: dict, batch) -> dict:
        self.validate_batch(project, batch)
        return self.approvals.require_approved(project["project_id"], "execution_approval", canonical_hash(batch.model_dump(mode="json")))
```

- [ ] **Step 3: Run tests and commit**

Run: `python -m pytest backend/tests/test_execution_policy.py backend/tests/test_project_environment_service.py -q`

Expected: PASS.

```powershell
git add backend/services/execution_policy.py backend/services/project_environment_service.py backend/tests/test_execution_policy.py backend/tests/test_project_environment_service.py
git commit -m "feat: bind experiment execution to approval"
```

### Task 4: Restricted Runner and Immutable Experiment Output

**Files:**
- Create: `backend/services/restricted_runner.py`
- Create: `backend/services/environment_capture.py`
- Create: `backend/services/experiment_service.py`
- Test: `backend/tests/test_restricted_runner.py`
- Test: `backend/tests/test_experiment_service.py`

**Interfaces:**
- Consumes: approved `ExecutionBatch`, `ExecutionPolicy`, `ModelingStore`, and `ArtifactService`.
- Produces: `ExperimentService.execute(project_id: str, experiment_id: str) -> dict`.

- [ ] **Step 1: Write failing timeout and secret-scrubbing tests**

```python
def test_runner_scrubs_secrets_and_caps_output(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "do-not-leak")
    result = RestrictedRunner().run([sys.executable, "-c", "import os; print(os.getenv('LLM_API_KEY')); print('x'*5000)"], tmp_path, 10, 1024, False)
    assert "do-not-leak" not in result.stdout
    assert len(result.stdout.encode("utf-8")) <= 1024


def test_runner_kills_timed_out_process(tmp_path):
    result = RestrictedRunner().run([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path, 1, 1024, False)
    assert result.error_code == "resource_error"
    assert result.timed_out is True
```

- [ ] **Step 2: Implement restricted environment and process-tree termination**

```python
import os
import subprocess
import psutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    error_code: str | None


class RestrictedRunner:
    SENSITIVE = ("KEY", "TOKEN", "SECRET", "PASSWORD", "AUTHORIZATION")

    def run(self, command: list[str], cwd: Path, timeout_seconds: int, max_output_bytes: int, network_allowed: bool, on_started=None) -> RunResult:
        env = {key: value for key, value in os.environ.items() if not any(word in key.upper() for word in self.SENSITIVE)}
        if not network_allowed:
            env["MODELING_NETWORK_DISABLED"] = "1"
            env["PYTHONPATH"] = str(cwd / ".workflow" / "runtime")
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if on_started is not None:
            on_started(process.pid)
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            limit = max_output_bytes
            return RunResult(process.returncode, stdout.encode()[:limit].decode(errors="replace"), stderr.encode()[:limit].decode(errors="replace"), False, None if process.returncode == 0 else "code_error")
        except subprocess.TimeoutExpired:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            process.communicate()
            return RunResult(-1, "", "Execution timed out", True, "resource_error")
```

Create `.workflow/runtime/sitecustomize.py` before a no-network run:

```python
import os
if os.getenv("MODELING_NETWORK_DISABLED") == "1":
    import socket
    def denied(*args, **kwargs):
        raise RuntimeError("Network access is disabled for this experiment")
    socket.socket = denied
    socket.create_connection = denied
```

- [ ] **Step 3: Implement experiment execution and artifact validation**

`ExperimentService.execute` must require approval, atomically set status `running`, pass an `on_started` callback that persists the child PID, execute each command in order, write `run.log`, require valid `metrics.json` as a list of `MetricRecord`, capture `python --version` plus `pip freeze` in `environment.json`, register metrics/log/environment and every file declared by `artifacts.json`, then set status `completed` and clears PID. Failure sets `failed` with one stable error code, clears PID, and never deletes the experiment directory.

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest backend/tests/test_restricted_runner.py backend/tests/test_experiment_service.py -q`

Expected: PASS.

```powershell
git add backend/services/restricted_runner.py backend/services/environment_capture.py backend/services/experiment_service.py backend/tests/test_restricted_runner.py backend/tests/test_experiment_service.py
git commit -m "feat: run approved experiments in restricted workspace"
```

### Task 5: Experiment Gates, API, and UI

**Files:**
- Modify: `backend/services/modeling_gate_service.py`
- Modify: `backend/api/modeling.py`
- Test: `backend/tests/test_experiment_api.py`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/services/api.test.ts`
- Create: `frontend/src/components/ExperimentApprovalCard.tsx`
- Create: `frontend/src/components/ExperimentApprovalCard.test.tsx`
- Create: `frontend/src/components/ExperimentRunPanel.tsx`
- Create: `frontend/src/components/ExperimentRunPanel.test.tsx`
- Modify: `frontend/src/views/ModelingProjectsView.tsx`

**Interfaces:**
- Produces: prepare, execution-approval, execute, list, and detail endpoints plus experiment UI.
- Consumes: Phase 3 services.

- [ ] **Step 1: Write failing result-gate and API tests**

```python
def test_result_gate_requires_baseline_candidate_and_metrics(gate_service, project):
    with pytest.raises(ValueError, match="completed baseline and candidate"):
        gate_service.require_exit(project["project_id"], "result_validation")


def test_execute_returns_conflict_for_stale_approval(fake_experiment_service):
    fake_experiment_service.execute.side_effect = ValueError("Required approval does not match current content")
    with pytest.raises(HTTPException) as raised:
        asyncio.run(modeling.execute_experiment("p-1", "exp-0001"))
    assert raised.value.status_code == 409
```

- [ ] **Step 2: Extend gates and endpoints**

Add routes:

```text
POST /projects/{project_id}/experiments/prepare
GET  /projects/{project_id}/experiments
GET  /projects/{project_id}/experiments/{experiment_id}
POST /projects/{project_id}/experiments/{experiment_id}/request-execution
POST /projects/{project_id}/experiments/{experiment_id}/execute
```

The result gate requires at least two completed experiments, one with `model.kind == "baseline"`, valid non-empty validation metrics, and at least one registered figure or table across completed experiments.

- [ ] **Step 3: Implement approval and run panels**

`ExperimentApprovalCard` shows code hash, input hashes, commands, timeout, output cap, network flag, dependency diff, and exact approval hash. `ExperimentRunPanel` polls only `prepared` or `running` experiments every 1500 ms, shows logs after completion, compares metrics, and links each figure to its artifact ID.

- [ ] **Step 4: Run focused and full verification**

Run: `python -m pytest backend/tests/test_execution_policy.py backend/tests/test_restricted_runner.py backend/tests/test_experiment_service.py backend/tests/test_experiment_api.py backend/tests/test_modeling_gate_service.py -q`

Expected: PASS.

Run: `Set-Location frontend; npm test -- --run src/services/api.test.ts src/components/ExperimentApprovalCard.test.tsx src/components/ExperimentRunPanel.test.tsx; npm run build`

Expected: tests and build pass.

- [ ] **Step 5: Commit the experiment workflow UI**

```powershell
git add backend/services/modeling_gate_service.py backend/api/modeling.py backend/tests/test_experiment_api.py frontend/src/services/api.ts frontend/src/services/api.test.ts frontend/src/components/ExperimentApprovalCard.tsx frontend/src/components/ExperimentApprovalCard.test.tsx frontend/src/components/ExperimentRunPanel.tsx frontend/src/components/ExperimentRunPanel.test.tsx frontend/src/views/ModelingProjectsView.tsx
git commit -m "feat: add approved experiment workflow"
```

### Task 6: Reproducibility Checkpoint

**Files:**
- No source changes expected.

**Interfaces:**
- Verifies immutable experiments, approval invalidation, and deterministic reruns.

- [ ] **Step 1: Prepare and approve a baseline batch**

Expected: the approval card hash equals the backend request hash and the experiment enters `prepared`.

- [ ] **Step 2: Execute baseline and candidate experiments**

Expected: both finish with `metrics.json`, `run.log`, `environment.json`, and registered figures.

- [ ] **Step 3: Create a new experiment with the same seed and configuration**

Expected: validation metrics match the original within `1e-9` for deterministic estimators; the original experiment directory remains byte-for-byte unchanged.

- [ ] **Step 4: Change one command argument after approval**

Expected: execution is rejected with HTTP 409 until a new execution approval is granted.

- [ ] **Step 5: Run full suites**

Run: `python -m pytest backend/tests -q`

Expected: all backend tests pass.

Run: `Set-Location frontend; npm test -- --run; npm run build`

Expected: all frontend tests and build pass.
