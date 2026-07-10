# Mathematical Modeling Phase 5 Delivery and Git Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate reproducibility, build a complete delivery manifest and code archive, scan the exact Git change set, display a safe diff, and create one user-approved commit in the independent competition repository.

**Architecture:** DeliveryService assembles only registered and policy-allowed artifacts. GitPolicyService uses argument-array subprocess calls and porcelain output; GitCommitService hashes an explicit file list, diff, manifest, and message into the commit approval payload.

**Tech Stack:** Python 3.10+, pathlib, hashlib, json, zipfile, subprocess, regex, existing artifact/approval services, FastAPI, React, TypeScript, Vitest.

## Global Constraints

- Complete Phases 1–4 and follow roadmap constraints.
- The delivery manifest includes paper PDF, paper source, code, dependency lock, experiment metadata, data manifest, and reproduction command.
- Large, sensitive, or license-restricted raw data is excluded by default; its manifest entry remains required.
- Git stages only an explicit project-relative file list. Never run `git add .` or `git add -A`.
- Reject secrets, files larger than 20 MiB, `.env`, virtual environments, caches, build temporaries, and project-external symlinks.
- Commit approval binds manifest hash, staged file hashes, normalized diff hash, and commit message.

---

## File Map

- Create `backend/services/delivery_contracts.py`.
- Create `backend/services/reproducibility_service.py`.
- Create `backend/services/delivery_service.py`.
- Create `backend/services/git_policy_service.py`.
- Create `backend/services/git_commit_service.py`.
- Modify `backend/services/modeling_store.py`: project commit records.
- Modify `backend/services/modeling_gate_service.py`: package and commit gates.
- Modify `backend/services/output_service.py`: register final modeling output link without duplicating files.
- Modify `backend/api/modeling.py`: delivery and Git routes.
- Create backend tests for manifest, reproducibility, Git policy, Git commit, and API.
- Modify `frontend/src/services/api.ts` and tests.
- Create `frontend/src/components/DeliveryChecklist.tsx` and test.
- Create `frontend/src/components/GitCommitApprovalCard.tsx` and test.
- Modify `frontend/src/views/ModelingProjectsView.tsx`.

### Task 1: Reproducibility and Delivery Contracts

**Files:**
- Create: `backend/services/delivery_contracts.py`
- Create: `backend/services/reproducibility_service.py`
- Test: `backend/tests/test_reproducibility_service.py`

**Interfaces:**
- Produces: `DeliveryManifest`, `ReproductionCheck`, and `check(project_id: str) -> dict`.
- Consumes: project artifact index, experiment records, paper claims, and filesystem.

- [ ] **Step 1: Write failing reproducibility tests**

```python
def test_check_requires_pdf_code_dependencies_and_completed_experiments(checker, project):
    result = checker.check(project["project_id"])
    assert result["ok"] is False
    assert {item["code"] for item in result["issues"]} >= {"missing_pdf", "missing_reproduce_command"}


def test_check_detects_artifact_hash_mismatch(checker, project, registered_artifact):
    Path(project["workspace_path"], registered_artifact["relative_path"]).write_text("changed", encoding="utf-8")
    result = checker.check(project["project_id"])
    assert "artifact_hash_mismatch" in {item["code"] for item in result["issues"]}
```

- [ ] **Step 2: Define delivery contracts**

```python
from pydantic import BaseModel


class DeliveryFile(BaseModel):
    relative_path: str
    sha256: str
    size: int
    role: str
    included_in_git: bool
    exclusion_reason: str | None = None


class ReproductionIssue(BaseModel):
    code: str
    message: str
    blocking: bool


class ReproductionCheck(BaseModel):
    ok: bool
    issues: list[ReproductionIssue]


class DeliveryManifest(BaseModel):
    project_id: str
    generated_at: str
    reproduction_command: list[str]
    files: list[DeliveryFile]
    experiment_ids: list[str]
    paper_claim_count: int
```

- [ ] **Step 3: Implement deterministic checks**

`ReproducibilityService.check` verifies: `deliverables/paper.pdf`; `paper/draft.md`; `paper/main.tex`; `requirements.txt`; `reproduce.ps1`; non-empty `src`; at least two completed experiments; every registered artifact hash; all paper claim targets; and every experiment's config, metrics, environment, and log. Each failure returns a stable issue code and no raw secret value.

Use this result construction:

```python
issues = self._collect_issues(project_id)
return ReproductionCheck(ok=not any(item.blocking for item in issues), issues=issues).model_dump(mode="json")
```

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest backend/tests/test_reproducibility_service.py -q`

Expected: PASS.

```powershell
git add backend/services/delivery_contracts.py backend/services/reproducibility_service.py backend/tests/test_reproducibility_service.py
git commit -m "feat: validate modeling reproducibility"
```

### Task 2: Delivery Manifest, Code Archive, and Output Link

**Files:**
- Create: `backend/services/delivery_service.py`
- Modify: `backend/services/output_service.py`
- Test: `backend/tests/test_delivery_service.py`
- Test: `backend/tests/test_modeling_output_link.py`

**Interfaces:**
- Consumes: a passing reproduction check and artifact metadata.
- Produces: `build(project_id: str) -> dict`, `deliverables/manifest.json`, `deliverables/code.zip`, and an Outputs link record.

- [ ] **Step 1: Write failing archive policy tests**

```python
def test_archive_contains_code_not_raw_data(delivery_service, project):
    result = delivery_service.build(project["project_id"])
    with zipfile.ZipFile(Path(project["workspace_path"]) / "deliverables/code.zip") as archive:
        names = set(archive.namelist())
    assert "src/train.py" in names
    assert "requirements.txt" in names
    assert not any(name.startswith("data/raw/") for name in names)
    assert result["manifest_artifact"]["artifact_type"] == "delivery_manifest"
```

- [ ] **Step 2: Implement sorted deterministic archive creation**

```python
ARCHIVE_ROOTS = ("src", "tests", "paper", "analysis")
ARCHIVE_FILES = ("README.md", "requirements.txt", "reproduce.ps1")

with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    candidates = [path for root_name in ARCHIVE_ROOTS for path in (workspace / root_name).rglob("*") if path.is_file()]
    candidates.extend(workspace / name for name in ARCHIVE_FILES if (workspace / name).is_file())
    for path in sorted(candidates, key=lambda item: item.relative_to(workspace).as_posix()):
        archive.write(path, path.relative_to(workspace).as_posix())
```

Build the manifest after the archive, include excluded raw data entries from `data_manifest.json`, write canonical sorted JSON, and register both files. Add an Output record whose Markdown content stores the project ID and manifest artifact ID as explicit links; do not add an output-table column and do not copy the PDF into the application database.

- [ ] **Step 3: Run tests and commit**

Run: `python -m pytest backend/tests/test_delivery_service.py backend/tests/test_modeling_output_link.py -q`

Expected: PASS.

```powershell
git add backend/services/delivery_service.py backend/services/output_service.py backend/tests/test_delivery_service.py backend/tests/test_modeling_output_link.py
git commit -m "feat: package modeling deliverables"
```

### Task 3: Git Policy Scan and Reviewable Diff

**Files:**
- Create: `backend/services/git_policy_service.py`
- Test: `backend/tests/test_git_policy_service.py`

**Interfaces:**
- Produces: `status(project_id: str) -> dict`, `review(project_id: str, paths: list[str]) -> dict`, and `validate_paths`.
- Consumes: independent project workspace path only.

- [ ] **Step 1: Write failing unsafe-file tests**

```python
def test_policy_rejects_secret_and_large_file(policy, git_project):
    (git_project / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (git_project / "large.bin").write_bytes(b"x" * (20 * 1024 * 1024 + 1))
    review = policy.review({"workspace_path": str(git_project)}, [".env", "large.bin"])
    assert review["ok"] is False
    assert {issue["code"] for issue in review["issues"]} == {"forbidden_path", "file_too_large"}


def test_policy_rejects_project_external_symlink(policy, git_project, tmp_path):
    external = tmp_path / "secret.txt"
    external.write_text("secret", encoding="utf-8")
    link = git_project / "linked.txt"
    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip("symlink creation is unavailable on this Windows host")
    assert policy.review({"workspace_path": str(git_project)}, ["linked.txt"])["ok"] is False
```

- [ ] **Step 2: Implement explicit path normalization and scanners**

```python
FORBIDDEN_PARTS = {".env", ".venv", "__pycache__", ".pytest_cache", ".workflow/build"}
SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password|authorization)\s*[:=]\s*[^\s]+")
MAX_GIT_FILE_BYTES = 20 * 1024 * 1024


def resolve_git_path(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute():
        raise ValueError("Git path must be project-relative")
    target = (root / relative).resolve()
    if target == root or root not in target.parents:
        raise ValueError("Git path escapes project workspace")
    return target
```

For each requested file, reject forbidden parts, missing files, external symlinks, oversized content, and `SECRET_PATTERN` matches in UTF-8-decodable files. Run `git status --porcelain=v1 --untracked-files=all`. For tracked paths run `git diff --no-ext-diff --binary --` followed by the sorted path arguments; for untracked UTF-8 text construct a `difflib.unified_diff` from an empty file to its content, and list binary files by name and SHA-256. Cap combined review output at 2 MiB.

- [ ] **Step 3: Run tests and commit**

Run: `python -m pytest backend/tests/test_git_policy_service.py -q`

Expected: PASS.

```powershell
git add backend/services/git_policy_service.py backend/tests/test_git_policy_service.py
git commit -m "feat: scan modeling project Git changes"
```

### Task 4: Approval-Gated Explicit Git Commit

**Files:**
- Create: `backend/services/git_commit_service.py`
- Modify: `backend/services/modeling_store.py`
- Modify: `backend/services/modeling_gate_service.py`
- Test: `backend/tests/test_git_commit_service.py`
- Test: `backend/tests/test_commit_gate.py`

**Interfaces:**
- Consumes: Git policy review, delivery manifest, `ApprovalService`, explicit paths, and commit message.
- Produces: `request_commit` and `commit`; persists commit hash and payload hash.

- [ ] **Step 1: Write failing explicit-add and stale-approval tests**

```python
def test_commit_adds_only_approved_paths(commit_service, project, approved_request, fake_git):
    result = commit_service.commit(project["project_id"], ["README.md", "deliverables/manifest.json"], "feat: add modeling solution")
    assert fake_git.commands[0] == ["git", "add", "--", "README.md", "deliverables/manifest.json"]
    assert result["commit_hash"] == "abc123"


def test_commit_rejects_changed_message(commit_service, project, approved_request):
    with pytest.raises(ValueError, match="approval"):
        commit_service.commit(project["project_id"], approved_request["paths"], "different message")
```

- [ ] **Step 2: Add project commit persistence**

Add table:

```python
conn.execute("CREATE TABLE IF NOT EXISTS project_commits (record_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, approval_payload_hash TEXT NOT NULL, commit_hash TEXT NOT NULL, commit_message TEXT NOT NULL, manifest_hash TEXT NOT NULL, created_at TEXT NOT NULL)")
```

- [ ] **Step 3: Implement request and commit payload**

```python
payload = {
    "paths": sorted(paths),
    "file_hashes": self.policy.file_hashes(project, paths),
    "diff_hash": hashlib.sha256(review["diff"].encode("utf-8")).hexdigest(),
    "manifest_hash": manifest_artifact["sha256"],
    "commit_message": message.strip(),
}
```

`request_commit` rejects an empty/over-72-character subject, requires a passing policy review and reproduction check, and requests `commit_approval`. `commit` rebuilds the payload, requires matching approval, invokes `git add --` with the sorted approved paths as separate arguments, verifies `git diff --cached --quiet` returns nonzero, invokes `git commit -m` with the approved message as a separate argument, reads `git rev-parse HEAD`, persists the commit record, and never invokes a remote.

- [ ] **Step 4: Extend gates, run tests, and commit**

The `packaging` exit requires a registered delivery manifest and passing reproduction check. The `commit_approval_pending` exit requires matching commit approval. The `committing` exit requires a persisted commit record for the current manifest hash.

Run: `python -m pytest backend/tests/test_git_commit_service.py backend/tests/test_commit_gate.py -q`

Expected: PASS.

```powershell
git add backend/services/git_commit_service.py backend/services/modeling_store.py backend/services/modeling_gate_service.py backend/tests/test_git_commit_service.py backend/tests/test_commit_gate.py
git commit -m "feat: commit approved modeling deliverables"
```

### Task 5: Delivery and Git API/UI

**Files:**
- Modify: `backend/api/modeling.py`
- Test: `backend/tests/test_delivery_git_api.py`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/services/api.test.ts`
- Create: `frontend/src/components/DeliveryChecklist.tsx`
- Create: `frontend/src/components/DeliveryChecklist.test.tsx`
- Create: `frontend/src/components/GitCommitApprovalCard.tsx`
- Create: `frontend/src/components/GitCommitApprovalCard.test.tsx`
- Modify: `frontend/src/views/ModelingProjectsView.tsx`

**Interfaces:**
- Produces: build/check/diff/request/commit endpoints and final delivery UI.

- [ ] **Step 1: Add routes with conflict-safe error mapping**

```text
POST /projects/{project_id}/deliverables/check
POST /projects/{project_id}/deliverables/build
GET  /projects/{project_id}/deliverables
POST /projects/{project_id}/git/review
POST /projects/{project_id}/git/request-commit
POST /projects/{project_id}/git/commit
```

Request bodies use explicit `paths: list[str]` and `commit_message: str`. Stale approval, dirty payload, or failed policy review returns 409; missing project returns 404; invalid paths return 400.

- [ ] **Step 2: Write failing commit-card test**

```typescript
it('submits the exact reviewed paths and message', async () => {
  render(<GitCommitApprovalCard projectId="p-1" review={{ ok: true, paths: ['README.md'], diff: 'diff', issues: [] }} />)
  fireEvent.change(screen.getByLabelText('Commit message'), { target: { value: 'feat: add modeling solution' } })
  fireEvent.click(screen.getByRole('button', { name: 'Request commit approval' }))
  await waitFor(() => expect(modelingApi.requestCommit).toHaveBeenCalledWith('p-1', { paths: ['README.md'], commit_message: 'feat: add modeling solution' }))
})
```

- [ ] **Step 3: Implement delivery and commit cards**

`DeliveryChecklist` lists every required item, hash status, Git inclusion, and exclusion reason, and disables Build until reproduction passes. `GitCommitApprovalCard` loads porcelain status, lets the user choose only policy-allowed files, displays the capped diff and issues, requests approval, and exposes Commit only when the returned approval hash matches the current review payload.

- [ ] **Step 4: Run verification and commit**

Run: `python -m pytest backend/tests/test_delivery_git_api.py backend/tests/test_delivery_service.py backend/tests/test_git_policy_service.py backend/tests/test_git_commit_service.py -q`

Expected: PASS.

Run: `Set-Location frontend; npm test -- --run src/services/api.test.ts src/components/DeliveryChecklist.test.tsx src/components/GitCommitApprovalCard.test.tsx; npm run build`

Expected: tests and build pass.

```powershell
git add backend/api/modeling.py backend/tests/test_delivery_git_api.py frontend/src/services/api.ts frontend/src/services/api.test.ts frontend/src/components/DeliveryChecklist.tsx frontend/src/components/DeliveryChecklist.test.tsx frontend/src/components/GitCommitApprovalCard.tsx frontend/src/components/GitCommitApprovalCard.test.tsx frontend/src/views/ModelingProjectsView.tsx
git commit -m "feat: add modeling delivery and commit review"
```

### Task 6: Phase 5 Independent-Repository Checkpoint

**Files:**
- No source changes expected.

**Interfaces:**
- Verifies final packaging and commit safety.

- [ ] **Step 1: Build deliverables for the fixture project**

Expected: manifest, code archive, PDF, sources, dependency lock, experiment list, data exclusions, and reproduction command are present.

- [ ] **Step 2: Add a fake secret and oversized file**

Expected: both appear as blocking Git review issues and cannot be selected for approval.

- [ ] **Step 3: Remove unsafe files, review exact paths, and approve**

Expected: approval payload hashes the same paths, file contents, diff, manifest, and commit message shown in the UI.

- [ ] **Step 4: Modify one staged file after approval**

Expected: commit returns 409 and stages nothing until review and approval are repeated.

- [ ] **Step 5: Commit and inspect repository history**

Run inside the generated project: `git log -1 --oneline`

Expected: one commit with the approved message; `git remote -v` remains empty.
