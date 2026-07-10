# Mathematical Modeling Phase 6 Recovery and Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the complete modeling workflow recover after interruption, expose runtime readiness, enforce adversarial resource/path/network checks, and repeatedly pass one fixed end-to-end competition fixture.

**Architecture:** Recovery reconciles SQLite state with immutable filesystem evidence at startup instead of blindly rerunning work. Runtime diagnostics report capability without leaking local secrets; a deterministic fixture drives service-level and UI integration tests across all six phases.

**Tech Stack:** Python 3.10+, FastAPI startup lifecycle, SQLite, pathlib, psutil, pytest, React, TypeScript, Vitest, Testing Library, local Git, XeLaTeX.

## Global Constraints

- Complete Phases 1–5 and follow roadmap constraints.
- Recovery never silently marks a running task completed; it records interruption and returns to the last safe recoverable state.
- Startup reconciliation must be idempotent.
- Runtime diagnostics expose booleans and version strings, never environment-variable values, API keys, or unrestricted absolute paths.
- The regression fixture is small, deterministic, UTF-8, and licensed for inclusion in the repository.
- The E2E test uses fake deterministic LLM responses and real CSV, filesystem, SQLite, Python execution, XeLaTeX when available, and Git.

---

## File Map

- Create `backend/services/modeling_recovery_service.py`.
- Create `backend/services/modeling_runtime_status.py`.
- Modify `backend/services/modeling_store.py`: workflow task/run interruption fields and queries.
- Modify `backend/main.py`: startup reconciliation.
- Modify `backend/api/modeling.py`: runtime and recovery endpoints.
- Create `backend/tests/test_modeling_recovery_service.py`.
- Create `backend/tests/test_modeling_runtime_status.py`.
- Create `backend/tests/test_modeling_security_regression.py`.
- Create `backend/tests/fixtures/modeling_competition/problem.txt`.
- Create `backend/tests/fixtures/modeling_competition/train.csv`.
- Create `backend/tests/fixtures/modeling_competition/expected_contracts.json`.
- Create `backend/tests/fakes/fake_modeling_llm.py`.
- Create `backend/tests/test_modeling_workflow_e2e.py`.
- Modify `frontend/src/services/api.ts` and tests.
- Create `frontend/src/components/ModelingRuntimeStatus.tsx` and test.
- Create `frontend/src/components/ModelingRecoveryBanner.tsx` and test.
- Create `frontend/src/views/ModelingWorkflow.integration.test.tsx`.
- Modify `frontend/src/views/ModelingProjectsView.tsx`.
- Modify `README.md` and `TESTING_GUIDE.md`.

### Task 1: Idempotent Startup Recovery

**Files:**
- Create: `backend/services/modeling_recovery_service.py`
- Modify: `backend/services/modeling_store.py`
- Modify: `backend/main.py`
- Modify: `backend/api/modeling.py`
- Test: `backend/tests/test_modeling_recovery_service.py`

**Interfaces:**
- Produces: `recover_interrupted_projects() -> list[dict]`.
- Consumes: project state, workflow tasks, experiment records, workspace evidence, and transition history.

- [ ] **Step 1: Write failing interruption tests**

```python
def test_recovery_marks_running_experiment_interrupted_and_returns_safe_state(recovery, store, project):
    store.update_state(project["project_id"], "experiment_running")
    store.create_experiment(project["project_id"], "exp-0001", {}, "running")
    result = recovery.recover_interrupted_projects()
    assert result[0]["recovered_to"] == "experiment_implementation"
    assert store.get_experiment("exp-0001")["error_code"] == "interrupted"


def test_recovery_is_idempotent(recovery, store, project):
    store.update_state(project["project_id"], "committing")
    first = recovery.recover_interrupted_projects()
    second = recovery.recover_interrupted_projects()
    assert len(first) == 1
    assert second == []
```

- [ ] **Step 2: Add interruption queries and records**

Add a `workflow_recoveries` table with recovery ID, project ID, from/to states, interrupted run IDs, created time, and dismissed time. Add `list_projects_in_states(states: list[str])`, `active_experiments(project_id: str)`, `mark_experiment_interrupted(experiment_id: str)`, `latest_transition(project_id: str)`, `create_recovery`, `list_recoveries`, and `dismiss_recovery` to `ModelingStore`. Update only rows with status `running`; use a transaction to write the interruption, recovery record, and rollback transition together.

- [ ] **Step 3: Implement recovery mapping**

```python
from pathlib import Path
import psutil


RECOVERY_TARGETS = {
    "problem_parsing": "project_initialized",
    "data_profiling": "problem_parsing",
    "model_planning": "data_profiling",
    "experiment_implementation": "model_planning",
    "experiment_running": "experiment_implementation",
    "result_validation": "experiment_implementation",
    "paper_drafting": "result_validation",
    "consistency_review": "paper_drafting",
    "packaging": "paper_drafting",
    "committing": "packaging",
}


class ModelingRecoveryService:
    def __init__(self, store):
        self.store = store

    def recover_interrupted_projects(self) -> list[dict]:
        recovered = []
        for project in self.store.list_projects_in_states(list(RECOVERY_TARGETS)):
            if not self.store.project_has_active_run(project["project_id"]):
                continue
            for experiment in self.store.active_experiments(project["project_id"]):
                self._stop_owned_process(project, experiment.get("pid"))
            target = RECOVERY_TARGETS[project["state"]]
            self.store.interrupt_active_runs_and_transition(project["project_id"], project["state"], target)
            recovered.append({"project_id": project["project_id"], "recovered_from": project["state"], "recovered_to": target})
        return recovered

    @staticmethod
    def _stop_owned_process(project: dict, pid: int | None) -> None:
        if not pid or not psutil.pid_exists(pid):
            return
        process = psutil.Process(pid)
        command = " ".join(process.cmdline()).lower()
        workspace = str(Path(project["workspace_path"]).resolve()).lower()
        if workspace not in command and Path(process.cwd()).resolve() != Path(project["workspace_path"]).resolve():
            raise RuntimeError("Refusing to terminate a process not owned by this project")
        for child in process.children(recursive=True):
            child.kill()
        process.kill()
```

Invoke once during FastAPI startup after settings are loaded. Log only project ID and state names.

Add `GET /api/modeling/recoveries` to return undismissed records and `POST /api/modeling/recoveries/{recovery_id}/dismiss` to timestamp dismissal without deleting history.

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest backend/tests/test_modeling_recovery_service.py backend/tests/test_startup_scripts.py -q`

Expected: PASS.

```powershell
git add backend/services/modeling_recovery_service.py backend/services/modeling_store.py backend/main.py backend/api/modeling.py backend/tests/test_modeling_recovery_service.py
git commit -m "feat: recover interrupted modeling workflows"
```

### Task 2: Runtime Capability Diagnostics

**Files:**
- Create: `backend/services/modeling_runtime_status.py`
- Modify: `backend/api/modeling.py`
- Test: `backend/tests/test_modeling_runtime_status.py`

**Interfaces:**
- Produces: `status() -> dict` and `GET /api/modeling/runtime`.
- Consumes: configured workspace root and safe executable probes.

- [ ] **Step 1: Write failing redaction and capability tests**

```python
def test_status_reports_tools_without_secrets(monkeypatch, status_service):
    monkeypatch.setenv("LLM_API_KEY", "never-return-this")
    result = status_service.status()
    assert set(result) == {"workspace", "python", "git", "xelatex"}
    assert "never-return-this" not in json.dumps(result)
    assert isinstance(result["git"]["available"], bool)
```

- [ ] **Step 2: Implement bounded probes**

```python
import shutil
import subprocess
import sys
import os
from pathlib import Path


def probe(command: list[str]) -> dict:
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False, "version": None}
    result = subprocess.run([executable, *command[1:]], capture_output=True, text=True, timeout=5)
    line = (result.stdout or result.stderr).splitlines()[0][:200] if (result.stdout or result.stderr) else ""
    return {"available": result.returncode == 0, "version": line}


class ModelingRuntimeStatus:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)

    def status(self) -> dict:
        writable = self.workspace_root.exists() and os.access(self.workspace_root, os.W_OK)
        return {
            "workspace": {"configured": True, "writable": writable},
            "python": {"available": True, "version": sys.version.split()[0]},
            "git": probe(["git", "--version"]),
            "xelatex": probe(["xelatex", "--version"]),
        }
```

- [ ] **Step 3: Add endpoint, run tests, and commit**

Run: `python -m pytest backend/tests/test_modeling_runtime_status.py backend/tests/test_settings_api.py -q`

Expected: PASS.

```powershell
git add backend/services/modeling_runtime_status.py backend/api/modeling.py backend/tests/test_modeling_runtime_status.py
git commit -m "feat: report modeling runtime readiness"
```

### Task 3: Adversarial Security and Resource Regression Suite

**Files:**
- Create: `backend/tests/test_modeling_security_regression.py`
- Modify: `backend/services/restricted_runner.py`
- Modify: `backend/services/git_policy_service.py`
- Modify: `backend/services/modeling_input_service.py`

**Interfaces:**
- Verifies all security boundaries implemented in Phases 2, 3, and 5.
- Produces: stable `policy_error` or `resource_error` outcomes for every adversarial case.

- [ ] **Step 1: Add parameterized adversarial cases**

```python
@pytest.mark.parametrize("relative", ["../escape.txt", "C:/Windows/win.ini", "/etc/passwd", "data/raw/../../secret"])
def test_all_file_services_reject_escape(relative, security_harness):
    for service in security_harness.path_services:
        with pytest.raises(ValueError):
            service.resolve_write_target(security_harness.project, relative)


@pytest.mark.parametrize("name", ["LLM_API_KEY", "AUTHORIZATION", "ACCESS_TOKEN", "DB_PASSWORD"])
def test_runner_never_forwards_sensitive_environment(name, monkeypatch, restricted_runner, tmp_path):
    monkeypatch.setenv(name, "sensitive-value")
    result = restricted_runner.run([sys.executable, "-c", f"import os; print(os.getenv('{name}'))"], tmp_path, 10, 4096, False)
    assert "sensitive-value" not in result.stdout


def test_network_socket_is_denied(restricted_python_command, tmp_path):
    result = RestrictedRunner().run(restricted_python_command("import socket; socket.create_connection(('example.com', 80))"), tmp_path, 10, 4096, False)
    assert result.exit_code != 0
    assert "Network access is disabled" in result.stderr
```

- [ ] **Step 2: Add output, timeout, symlink, and Git command assertions**

Tests must cover 10 MiB output truncation, one-second timeout, child-process termination, external symlink rejection, forbidden Git paths, secret patterns, 20 MiB files, empty commit, stale approval, and proof that captured Git commands never contain `push`, `reset`, `clean`, `rebase`, `remote`, or `checkout`.

- [ ] **Step 3: Run the regression test and apply minimal fixes**

Run: `python -m pytest backend/tests/test_modeling_security_regression.py -q`

Expected: PASS with every parameterized attack blocked.

- [ ] **Step 4: Commit security hardening**

```powershell
git add backend/tests/test_modeling_security_regression.py backend/services/restricted_runner.py backend/services/git_policy_service.py backend/services/modeling_input_service.py
git commit -m "test: harden modeling execution boundaries"
```

### Task 4: Deterministic Competition Fixture and Fake LLM

**Files:**
- Create: `backend/tests/fixtures/modeling_competition/problem.txt`
- Create: `backend/tests/fixtures/modeling_competition/train.csv`
- Create: `backend/tests/fixtures/modeling_competition/expected_contracts.json`
- Create: `backend/tests/fakes/fake_modeling_llm.py`
- Test: `backend/tests/test_modeling_fixture.py`

**Interfaces:**
- Produces: a small regression problem with 24 rows, target `sales`, features `price`, `promotion`, and `weekday`; deterministic role responses.

- [ ] **Step 1: Create the fixture prompt**

```text
Build and compare a mean baseline and a linear-regression model that predicts sales from price, promotion, and weekday. Use a deterministic train/validation split, report validation RMSE and MAE, create one prediction-versus-actual figure, discuss limitations, and deliver a reproducible paper.
```

- [ ] **Step 2: Create the CSV and expected contract**

Use this exact `train.csv`:

```csv
price,promotion,weekday,sales
10,0,1,105
11,0,2,101
12,0,3,98
13,0,4,94
14,0,5,91
15,0,6,88
16,0,7,86
10,1,1,124
11,1,2,121
12,1,3,118
13,1,4,115
14,1,5,112
15,1,6,109
16,1,7,106
9,0,1,108
9,1,2,129
17,0,3,82
17,1,4,102
12,0,5,96
12,1,6,116
14,0,7,89
14,1,1,114
11,0,4,100
15,1,5,110
```

Use this exact `expected_contracts.json`:

```json
{
  "target": "sales",
  "features": ["price", "promotion", "weekday"],
  "seed": 42,
  "candidates": ["mean_baseline", "linear_regression"],
  "validation_metrics": ["rmse", "mae"],
    "required_artifact_type": "figure",
  "row_count": 24
}
```

- [ ] **Step 3: Implement stage-keyed fake responses**

```python
import json
import re


class FakeModelingLLM:
    def __init__(self, responses: dict[str, dict]):
        self.responses = responses
        self.stage = ""

    async def generate(self, prompt: str) -> str:
        for stage, payload in self.responses.items():
            if f"STAGE:{stage}" in prompt:
                rendered = json.loads(json.dumps(payload, ensure_ascii=False))
                if stage == "paper_writer":
                    match = re.search(r"PREDICTION_ARTIFACT_ID:([A-Za-z0-9-]+)", prompt)
                    if not match:
                        raise AssertionError("Paper prompt omitted prediction artifact ID")
                    rendered["markdown"] = rendered["markdown"].replace("artifact-prediction", match.group(1))
                return json.dumps(rendered, ensure_ascii=False)
        raise AssertionError("Prompt did not declare a known modeling stage")
```

Initialize the fake with these fully determined semantic responses; the programmer responses read their source strings from test constants `BASELINE_FILES` and `CANDIDATE_FILES`, which the fixture test executes before using them in the workflow:

```python
RESPONSES = {
    "problem_parser": {
        "title": "Sales forecasting",
        "subproblems": ["Build a baseline", "Build a regression model", "Compare validation metrics"],
        "objectives": ["Predict sales"],
        "constraints": ["Use a deterministic split"],
        "evaluation_requirements": ["validation RMSE", "validation MAE"],
        "deliverables": ["code", "prediction figure", "paper PDF"],
    },
    "model_planner": {
        "problem_summary": "Predict sales from price, promotion, and weekday.",
        "candidates": [
            {"name": "mean_baseline", "assumptions": ["validation target is unseen"], "features": ["price", "promotion", "weekday"], "algorithm": "training-target mean", "metrics": ["rmse", "mae"], "risks": ["underfitting"]},
            {"name": "linear_regression", "assumptions": ["effects are approximately additive"], "features": ["price", "promotion", "weekday"], "algorithm": "linear regression", "metrics": ["rmse", "mae"], "risks": ["nonlinear effects"]}
        ],
    },
    "paper_writer": {
        "markdown": "# Sales Forecasting\n\n## Problem\nWe compare two models.\n\n## Results\nValidation RMSE is {{metric:exp-0002.validation_rmse}} and MAE is {{metric:exp-0002.validation_mae}}. Figure: {{figure:artifact-prediction}}.\n\n## Limitations\nThe fixture is small and synthetic.\n",
        "latex": "\\documentclass{article}\n\\begin{document}\n\\section{Sales Forecasting}\nValidation RMSE is {{metric:exp-0002.validation_rmse}} and MAE is {{metric:exp-0002.validation_mae}}.\\end{document}\n"
    },
    "reviewer": {"issues": []}
}
```

`BASELINE_FILES` and `CANDIDATE_FILES` must each contain all seven allowed generated paths, call `train_test_split(frame, test_size=0.25, random_state=42)`, write `metrics.json` as validation `rmse` and `mae` records, and make the candidate write `figures/prediction.png` plus an `artifacts.json` entry with type `figure`. `test_modeling_fixture.py` imports these constants, writes them to a temporary project, runs `pytest tests/test_pipeline.py`, and executes the declared commands; this prevents an untested fixture response from reaching the E2E test.

- [ ] **Step 4: Validate fixture and commit**

Run: `python -m pytest backend/tests/test_modeling_fixture.py -q`

Expected: PASS and confirm 24 data rows.

```powershell
git add backend/tests/fixtures/modeling_competition/problem.txt backend/tests/fixtures/modeling_competition/train.csv backend/tests/fixtures/modeling_competition/expected_contracts.json backend/tests/fakes/fake_modeling_llm.py backend/tests/test_modeling_fixture.py
git commit -m "test: add deterministic modeling competition fixture"
```

### Task 5: Full Backend Workflow E2E

**Files:**
- Create: `backend/tests/test_modeling_workflow_e2e.py`

**Interfaces:**
- Consumes: every service from Phases 1–6 and the deterministic fixture.
- Produces: one test proving the complete workflow and one proving restart recovery.

- [ ] **Step 1: Write the full workflow test**

```python
def test_modeling_workflow_produces_traceable_pdf_and_commit(modeling_harness):
    project = modeling_harness.create_project("Fixture Forecast")
    modeling_harness.import_fixture(project)
    modeling_harness.parse_profile_and_plan(project)
    modeling_harness.approve_current(project, "model_approval")
    modeling_harness.prepare_approve_and_run(project, candidate_index=0)
    modeling_harness.prepare_approve_and_run(project, candidate_index=1)
    modeling_harness.validate_results(project)
    modeling_harness.write_and_review_paper(project)
    modeling_harness.approve_current(project, "final_approval")
    modeling_harness.compile_paper(project)
    modeling_harness.build_deliverables(project)
    modeling_harness.review_and_approve_commit(project, "feat: add fixture modeling solution")
    result = modeling_harness.commit(project)
    assert result["state"] == "completed"
    assert modeling_harness.unresolved_claims(project) == []
    assert modeling_harness.git_log(project, 1)[0]["subject"] == "feat: add fixture modeling solution"
```

- [ ] **Step 2: Write restart recovery test**

Create a project, persist `experiment_running`, start a subprocess that sleeps, invoke recovery as if the app restarted, and assert the process is terminated, the experiment is `failed/interrupted`, the project returns to `experiment_implementation`, and the next prepared experiment uses a new ID.

- [ ] **Step 3: Run E2E with XeLaTeX capability handling**

Run: `python -m pytest backend/tests/test_modeling_workflow_e2e.py -q`

Expected: PASS when XeLaTeX is installed. If unavailable, only the compilation test is skipped with reason `xelatex is not installed`; all paper rendering and approval assertions still run.

- [ ] **Step 4: Commit backend E2E coverage**

```powershell
git add backend/tests/test_modeling_workflow_e2e.py
git commit -m "test: cover end-to-end modeling workflow"
```

### Task 6: Runtime and Recovery UI Integration

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/services/api.test.ts`
- Create: `frontend/src/components/ModelingRuntimeStatus.tsx`
- Create: `frontend/src/components/ModelingRuntimeStatus.test.tsx`
- Create: `frontend/src/components/ModelingRecoveryBanner.tsx`
- Create: `frontend/src/components/ModelingRecoveryBanner.test.tsx`
- Create: `frontend/src/views/ModelingWorkflow.integration.test.tsx`
- Modify: `frontend/src/views/ModelingProjectsView.tsx`

**Interfaces:**
- Produces: runtime readiness, recovery notices, and a mocked UI journey through every gate.

- [ ] **Step 1: Add typed runtime and recovery API methods**

```typescript
export interface ModelingRuntimeStatus {
  workspace: { configured: boolean; writable: boolean }
  python: { available: boolean; version: string | null }
  git: { available: boolean; version: string | null }
  xelatex: { available: boolean; version: string | null }
}

runtime: async (): Promise<ModelingRuntimeStatus> => (await api.get('/modeling/runtime')).data,
recoveries: async (): Promise<{ recoveries: Array<{ project_id: string; recovered_from: string; recovered_to: string }> }> => (await api.get('/modeling/recoveries')).data,
```

- [ ] **Step 2: Implement status and recovery components**

`ModelingRuntimeStatus` shows Ready/Unavailable for workspace, Python, Git, and XeLaTeX and disables only actions requiring a missing capability. `ModelingRecoveryBanner` states the previous and recovered stage, links to the interrupted run, and can be dismissed without deleting the recovery record.

- [ ] **Step 3: Add the UI integration journey**

Mock modeling API responses through project creation, input, plan approval, two experiments, paper review, final approval, compilation, packaging, Git approval, and completion. Assert each approval button appears only at its declared state and stale content removes the approval action.

- [ ] **Step 4: Run frontend tests and commit**

Run: `Set-Location frontend; npm test -- --run src/components/ModelingRuntimeStatus.test.tsx src/components/ModelingRecoveryBanner.test.tsx src/views/ModelingWorkflow.integration.test.tsx; npm run build`

Expected: tests and build pass.

```powershell
git add frontend/src/services/api.ts frontend/src/services/api.test.ts frontend/src/components/ModelingRuntimeStatus.tsx frontend/src/components/ModelingRuntimeStatus.test.tsx frontend/src/components/ModelingRecoveryBanner.tsx frontend/src/components/ModelingRecoveryBanner.test.tsx frontend/src/views/ModelingWorkflow.integration.test.tsx frontend/src/views/ModelingProjectsView.tsx
git commit -m "feat: expose modeling recovery and runtime status"
```

### Task 7: Documentation and Release Verification

**Files:**
- Modify: `README.md`
- Modify: `TESTING_GUIDE.md`

**Interfaces:**
- Documents the complete user flow, local requirements, safety gates, data policy, recovery behavior, and exact verification commands.

- [ ] **Step 1: Document runtime prerequisites and the six-stage workflow**

Add Python 3.10+, Git, and XeLaTeX checks; the workspace-root setting; four approvals; supported input suffixes; raw-data policy; and the fixture workflow command.

- [ ] **Step 2: Run complete backend verification**

Run: `python -m pytest backend/tests -q`

Expected: all tests pass, with only the explicitly reasoned XeLaTeX skip allowed on machines without XeLaTeX.

- [ ] **Step 3: Run complete frontend verification**

Run: `Set-Location frontend; npm test -- --run; npm run build`

Expected: all tests pass and Vite production build succeeds.

- [ ] **Step 4: Run manual restart and Git safety audit**

Interrupt one experiment, restart, finish the fixture, inspect every approval hash, inspect `git remote -v`, and compare all paper claims to `artifact_index.json`.

Expected: recovery is visible, the workflow completes, no remote exists, and every claim resolves.

- [ ] **Step 5: Commit release documentation**

```powershell
git add README.md TESTING_GUIDE.md
git commit -m "docs: document mathematical modeling workflow"
```
