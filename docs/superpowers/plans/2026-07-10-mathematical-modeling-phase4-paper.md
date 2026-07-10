# Mathematical Modeling Phase 4 Paper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate an editable Markdown paper and formal LaTeX source whose experimental claims resolve only from registered artifacts, pass independent review, receive final approval, and compile to PDF.

**Architecture:** A placeholder resolver separates prose generation from experimental facts. Paper and review agents return validated structures; a final-paper payload binds Markdown, LaTeX, references, resolved facts, and review status before a restricted XeLaTeX service compiles.

**Tech Stack:** Python 3.10+, Pydantic, existing LLM service, pathlib, regex, subprocess, XeLaTeX, React Markdown, TypeScript, Vitest.

## Global Constraints

- Complete Phases 1–3 and follow roadmap constraints.
- Markdown remains editable; LaTeX is formal source; the PDF is generated only after final approval.
- Experimental numbers and figure/table references use concrete forms such as `{{metric:exp-0001.validation_rmse}}`, `{{figure:artifact-0032}}`, or `{{table:artifact-0033}}` until deterministic rendering.
- A placeholder resolves only to an artifact belonging to the same project and a completed experiment.
- The reviewer reports issues with severity `blocking`, `warning`, or `info` and never silently edits files.
- XeLaTeX runs with `-no-shell-escape -interaction=nonstopmode -halt-on-error` from `paper/`.

---

## File Map

- Create `backend/services/paper_contracts.py`.
- Create `backend/services/paper_claim_service.py`.
- Create `backend/services/paper_placeholder_service.py`.
- Create `backend/services/paper_agent_service.py`.
- Create `backend/services/review_agent_service.py`.
- Create `backend/services/latex_service.py`.
- Modify `backend/services/modeling_store.py`: paper claims and review records.
- Modify `backend/services/modeling_gate_service.py`: paper/review/final gates.
- Modify `backend/api/modeling.py`: paper routes.
- Create `backend/skills/modeling_paper_writer/skill.json`.
- Create `backend/skills/modeling_reviewer/skill.json`.
- Create focused backend tests.
- Modify `frontend/src/services/api.ts` and tests.
- Create `frontend/src/components/PaperWorkspace.tsx` and test.
- Create `frontend/src/components/ReviewIssuesPanel.tsx` and test.
- Create `frontend/src/components/FinalPaperApprovalCard.tsx` and test.
- Modify `frontend/src/views/ModelingProjectsView.tsx`.

### Task 1: Paper Contracts, Claims, and Placeholder Resolution

**Files:**
- Create: `backend/services/paper_contracts.py`
- Create: `backend/services/paper_claim_service.py`
- Create: `backend/services/paper_placeholder_service.py`
- Modify: `backend/services/modeling_store.py`
- Test: `backend/tests/test_paper_placeholder_service.py`
- Test: `backend/tests/test_paper_claim_service.py`

**Interfaces:**
- Produces: `PaperClaim`, `ReviewIssue`, `resolve_markdown(project_id: str, markdown: str) -> tuple[str, list[dict]]`, and persisted claim links.
- Consumes: project artifacts and completed experiment records.

- [ ] **Step 1: Write failing resolution tests**

```python
def test_resolves_registered_metric_and_records_claim(resolver, project, completed_metric):
    rendered, claims = resolver.resolve_markdown(project["project_id"], "RMSE is {{metric:exp-0001.validation_rmse}}.")
    assert rendered == "RMSE is 1.25."
    assert claims[0]["experiment_id"] == "exp-0001"
    assert claims[0]["metric_name"] == "validation_rmse"


def test_rejects_unknown_or_incomplete_experiment(resolver, project):
    with pytest.raises(ValueError, match="Unresolvable paper placeholder"):
        resolver.resolve_markdown(project["project_id"], "{{metric:exp-9999.validation_rmse}}")
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest backend/tests/test_paper_placeholder_service.py backend/tests/test_paper_claim_service.py -q`

Expected: FAIL because paper services are missing.

- [ ] **Step 3: Define typed review and claim contracts**

```python
from typing import Literal
from pydantic import BaseModel


class PaperClaim(BaseModel):
    placeholder: str
    claim_type: Literal["metric", "figure", "table"]
    artifact_id: str
    experiment_id: str
    metric_name: str | None = None
    rendered_value: str


class ReviewIssue(BaseModel):
    severity: Literal["blocking", "warning", "info"]
    code: str
    message: str
    location: str
    artifact_ids: list[str]
```

Add `paper_claims` and `review_runs` tables. `paper_claims` stores `claim_id`, `project_id`, `paper_artifact_id`, `placeholder`, `claim_type`, `artifact_id`, `experiment_id`, `metric_name`, `rendered_value`, and `created_at`. `review_runs` stores `review_id`, `project_id`, `paper_hash`, `issues_json`, `status`, and `created_at`.

- [ ] **Step 4: Implement deterministic placeholder parsing**

```python
import json
import re
from decimal import Decimal
from pathlib import Path


TOKEN = re.compile(r"\{\{(metric|figure|table):([^}]+)\}\}")


class PaperPlaceholderService:
    def __init__(self, store, artifact_service):
        self.store = store
        self.artifacts = artifact_service

    def resolve_markdown(self, project_id: str, markdown: str) -> tuple[str, list[dict]]:
        claims = []
        def replace(match: re.Match) -> str:
            kind, reference = match.group(1), match.group(2)
            if kind == "metric":
                experiment_id, metric_name = reference.split(".", 1)
                experiment = self.store.get_experiment(experiment_id)
                if not experiment or experiment["project_id"] != project_id or experiment["status"] != "completed":
                    raise ValueError("Unresolvable paper placeholder")
                metric_artifact = next((item for item in self.store.list_artifacts(project_id) if item["source_experiment_id"] == experiment_id and item["artifact_type"] == "metrics"), None)
                if not metric_artifact:
                    raise ValueError("Unresolvable paper placeholder")
                project = self.store.get_project(project_id)
                payload = json.loads((Path(project["workspace_path"]) / metric_artifact["relative_path"]).read_text(encoding="utf-8"))
                record = next((item for item in payload if f"{item['split']}_{item['name']}" == metric_name), None)
                if not record:
                    raise ValueError("Unresolvable paper placeholder")
                value = format(Decimal(str(record["value"])), "f")
                claims.append({"placeholder": match.group(0), "claim_type": kind, "artifact_id": metric_artifact["artifact_id"], "experiment_id": experiment_id, "metric_name": metric_name, "rendered_value": value})
                return value
            artifact = self.artifacts.resolve(project_id, reference)
            if artifact["artifact_type"] != kind:
                raise ValueError("Unresolvable paper placeholder")
            claims.append({"placeholder": match.group(0), "claim_type": kind, "artifact_id": artifact["artifact_id"], "experiment_id": artifact["source_experiment_id"], "metric_name": None, "rendered_value": artifact["relative_path"]})
            return artifact["relative_path"]
        rendered = TOKEN.sub(replace, markdown)
        return rendered, claims
```

Persist each successful resolution set atomically:

```python
class PaperClaimService:
    def __init__(self, store):
        self.store = store

    def replace_for_paper(self, project_id: str, paper_artifact_id: str, claims: list[dict]) -> list[dict]:
        self.store.replace_paper_claims(project_id, paper_artifact_id, claims)
        return self.store.list_paper_claims(project_id, paper_artifact_id)
```

Add `replace_paper_claims(project_id, paper_artifact_id, claims)` to `ModelingStore`; it performs the delete and all inserts in one `_connect` transaction and assigns UUIDs plus timestamps. Add `list_paper_claims(project_id, paper_artifact_id=None)`; when the optional paper ID is absent it returns all project claims ordered by creation time.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest backend/tests/test_paper_placeholder_service.py backend/tests/test_paper_claim_service.py -q`

Expected: PASS.

```powershell
git add backend/services/paper_contracts.py backend/services/paper_claim_service.py backend/services/paper_placeholder_service.py backend/services/modeling_store.py backend/tests/test_paper_placeholder_service.py backend/tests/test_paper_claim_service.py
git commit -m "feat: bind paper claims to experiment artifacts"
```

### Task 2: Paper Writer Agent and Versioned Drafts

**Files:**
- Create: `backend/services/paper_agent_service.py`
- Create: `backend/skills/modeling_paper_writer/skill.json`
- Test: `backend/tests/test_paper_agent_service.py`

**Interfaces:**
- Consumes: problem specification, approved model plan, completed experiment artifacts, `LLMService.generate`, and Phase 2 `ModelingAgentRunService`.
- Produces: `create_draft(project_id: str) -> dict`, `paper/draft.md`, `paper/main.tex`, and registered paper artifacts.

- [ ] **Step 1: Write failing evidence-boundary tests**

```python
def test_writer_rejects_literal_experiment_number(writer, project):
    writer.llm.generate = AsyncMock(return_value=json.dumps({"markdown": "Validation RMSE was 1.25.", "latex": "Validation RMSE was 1.25."}))
    with pytest.raises(ValueError, match="must use metric placeholders"):
        asyncio.run(writer.create_draft(project["project_id"]))


def test_writer_accepts_metric_placeholder(writer, project):
    payload = {"markdown": "RMSE: {{metric:exp-0001.validation_rmse}}", "latex": "RMSE: {{metric:exp-0001.validation_rmse}}"}
    writer.llm.generate = AsyncMock(return_value=json.dumps(payload))
    result = asyncio.run(writer.create_draft(project["project_id"]))
    assert result["markdown_artifact"]["artifact_type"] == "paper_markdown"
```

- [ ] **Step 2: Implement the paper payload and numeric guard**

```python
import re
from pydantic import BaseModel, Field


class PaperDraftPayload(BaseModel):
    markdown: str = Field(min_length=100)
    latex: str = Field(min_length=100)


LITERAL_RESULT = re.compile(r"(?i)(rmse|mae|accuracy|precision|recall|f1|auc|r\^2)[^\n]{0,30}\b[0-9]+(?:\.[0-9]+)?")


def require_placeholder_results(text: str) -> None:
    scrubbed = re.sub(r"\{\{metric:[^}]+\}\}", "", text)
    if LITERAL_RESULT.search(scrubbed):
        raise ValueError("Experimental results must use metric placeholders")
```

`create_draft` sends the problem, approved plan, available artifact IDs, paper section requirements, and JSON schema to the LLM. It validates both strings, applies `require_placeholder_results`, writes with UTF-8, registers artifacts, and never resolves placeholders in the editable source.

- [ ] **Step 3: Add writer manifest**

```json
{"skill_id":"modeling_paper_writer","name":"Modeling Paper Writer","description":"Write Markdown and LaTeX from approved modeling artifacts.","allowed_tools":["retrieve_sources","create_output"],"prompt_template":"Return only JSON containing markdown and latex. Use supplied metric, figure, and table placeholders for every experimental fact; never type a measured value directly.","output_kind":"modeling_paper"}
```

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest backend/tests/test_paper_agent_service.py backend/tests/test_skill_service.py -q`

Expected: PASS.

```powershell
git add backend/services/paper_agent_service.py backend/skills/modeling_paper_writer/skill.json backend/tests/test_paper_agent_service.py
git commit -m "feat: generate evidence-bound modeling papers"
```

### Task 3: Independent Review and Paper Gates

**Files:**
- Create: `backend/services/review_agent_service.py`
- Create: `backend/skills/modeling_reviewer/skill.json`
- Modify: `backend/services/modeling_gate_service.py`
- Test: `backend/tests/test_review_agent_service.py`
- Test: `backend/tests/test_paper_gates.py`

**Interfaces:**
- Consumes: paper hash, resolved claims, problem spec, model plan, metrics, figures, LLM review output, and Phase 2 `ModelingAgentRunService`.
- Produces: `review(project_id: str) -> dict`; blocks final approval when any blocking issue exists.

- [ ] **Step 1: Write failing review tests**

```python
def test_review_combines_deterministic_and_llm_issues(reviewer, project):
    reviewer.llm.generate = AsyncMock(return_value=json.dumps({"issues": [{"severity": "warning", "code": "weak_limitations", "message": "Limitations are brief", "location": "Conclusion", "artifact_ids": []}]}))
    result = asyncio.run(reviewer.review(project["project_id"]))
    assert {item["code"] for item in result["issues"]} >= {"weak_limitations", "unresolved_placeholder"}


def test_final_gate_blocks_on_blocking_issue(gate_service, project):
    with pytest.raises(ValueError, match="blocking review issues"):
        gate_service.require_exit(project["project_id"], "final_approval_pending")
```

- [ ] **Step 2: Implement deterministic checks before LLM review**

The reviewer must add blocking issues for unresolved placeholders, missing subproblem headings, a paper artifact hash mismatch, claims pointing to incomplete experiments, missing figure files, and a LaTeX source without `\begin{document}` or `\end{document}`. It then asks the LLM only for semantic issues and validates every returned item as `ReviewIssue`.

Use this status rule:

```python
status = "failed" if any(issue.severity == "blocking" for issue in issues) else "passed"
self.store.create_review_run(project_id, paper_hash, [issue.model_dump(mode="json") for issue in issues], status)
```

- [ ] **Step 3: Extend paper gates**

```python
if state == "paper_drafting":
    self._require_artifact_types(project_id, {"paper_markdown", "paper_latex"})
if state == "consistency_review":
    review = self.store.latest_review(project_id)
    if not review or review["status"] != "passed":
        raise ValueError("Paper has blocking review issues")
if state == "final_approval_pending":
    payload_hash = self._current_paper_payload_hash(project_id)
    self.approval_service.require_approved(project_id, "final_approval", payload_hash)
```

- [ ] **Step 4: Add reviewer manifest and commit**

```json
{"skill_id":"modeling_reviewer","name":"Modeling Reviewer","description":"Independently review a traceable modeling paper without editing it.","allowed_tools":["retrieve_sources","create_output"],"prompt_template":"Return only structured review issues. Check subproblem coverage, assumptions, formulas, leakage, overfitting, result support, references, limitations, and reproducibility. Do not rewrite the paper.","output_kind":"paper_review"}
```

Run: `python -m pytest backend/tests/test_review_agent_service.py backend/tests/test_paper_gates.py backend/tests/test_skill_service.py -q`

Expected: PASS.

```powershell
git add backend/services/review_agent_service.py backend/services/modeling_gate_service.py backend/skills/modeling_reviewer/skill.json backend/tests/test_review_agent_service.py backend/tests/test_paper_gates.py
git commit -m "feat: add independent modeling paper review"
```

### Task 4: Final Approval and Restricted XeLaTeX Compilation

**Files:**
- Create: `backend/services/latex_service.py`
- Test: `backend/tests/test_latex_service.py`

**Interfaces:**
- Consumes: matching `final_approval`, placeholder resolver, and project paper files.
- Produces: `compile(project_id: str) -> dict`, resolved build sources under `.workflow/build/paper`, and `deliverables/paper.pdf`.

- [ ] **Step 1: Write failing command and stale-approval tests**

```python
def test_latex_command_disables_shell_escape(latex_service, project, approved_payload, fake_runner):
    latex_service.compile(project["project_id"])
    command = fake_runner.commands[0]
    assert "-no-shell-escape" in command
    assert "-halt-on-error" in command


def test_compile_rejects_changed_source(latex_service, project):
    (Path(project["workspace_path"]) / "paper/main.tex").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="approval"):
        latex_service.compile(project["project_id"])
```

- [ ] **Step 2: Implement isolated build and two-pass compilation**

```python
command = [
    "xelatex", "-no-shell-escape", "-interaction=nonstopmode",
    "-halt-on-error", "-output-directory", str(build_dir), str(build_main),
]
first = self.runner.run(command, paper_dir, 120, 2_000_000, False)
if first.exit_code != 0:
    raise ValueError("LaTeX compilation failed")
second = self.runner.run(command, paper_dir, 120, 2_000_000, False)
if second.exit_code != 0 or not (build_dir / "main.pdf").is_file():
    raise ValueError("LaTeX compilation failed")
shutil.copy2(build_dir / "main.pdf", workspace / "deliverables/paper.pdf")
```

Before compilation, copy the editable paper tree to `.workflow/build/paper`, resolve placeholders only in copied `.md`/`.tex` files, persist claims, and verify the current canonical payload hash against `final_approval`.

- [ ] **Step 3: Run tests and commit**

Run: `python -m pytest backend/tests/test_latex_service.py backend/tests/test_paper_placeholder_service.py -q`

Expected: PASS.

```powershell
git add backend/services/latex_service.py backend/tests/test_latex_service.py
git commit -m "feat: compile approved modeling papers"
```

### Task 5: Paper API and Workbench

**Files:**
- Modify: `backend/api/modeling.py`
- Test: `backend/tests/test_paper_api.py`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/services/api.test.ts`
- Create: `frontend/src/components/PaperWorkspace.tsx`
- Create: `frontend/src/components/PaperWorkspace.test.tsx`
- Create: `frontend/src/components/ReviewIssuesPanel.tsx`
- Create: `frontend/src/components/ReviewIssuesPanel.test.tsx`
- Create: `frontend/src/components/FinalPaperApprovalCard.tsx`
- Create: `frontend/src/components/FinalPaperApprovalCard.test.tsx`
- Modify: `frontend/src/views/ModelingProjectsView.tsx`

**Interfaces:**
- Produces: draft, save, review, final-approval, compile, and PDF-preview UI.

- [ ] **Step 1: Add paper endpoints**

```text
POST /projects/{project_id}/paper/draft
PUT  /projects/{project_id}/paper/markdown
POST /projects/{project_id}/paper/render
POST /projects/{project_id}/paper/review
GET  /projects/{project_id}/paper/reviews
POST /projects/{project_id}/paper/request-final-approval
POST /projects/{project_id}/paper/compile
GET  /projects/{project_id}/paper/pdf
```

Saving Markdown creates a new artifact version and invalidates prior reviews and final approval by changing the paper payload hash. PDF responses use `FileResponse` only after resolving the path from the project record.

- [ ] **Step 2: Write and run frontend paper tests**

```typescript
it('shows blocking review issues and disables final approval', async () => {
  render(<FinalPaperApprovalCard projectId="p-1" review={{ status: 'failed', issues: [{ severity: 'blocking', code: 'unresolved_placeholder', message: 'Missing metric', location: 'Results', artifact_ids: [] }] }} />)
  expect(screen.getByText('Missing metric')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Approve final paper' })).toBeDisabled()
})
```

Run: `Set-Location frontend; npm test -- --run src/components/PaperWorkspace.test.tsx src/components/ReviewIssuesPanel.test.tsx src/components/FinalPaperApprovalCard.test.tsx`

Expected: FAIL before components exist, then PASS after implementation.

- [ ] **Step 3: Implement the three-pane paper workspace**

The center pane edits Markdown with explicit Save, Review, Request approval, and Compile actions. The right pane lists claim provenance and review issues. The preview switches between rendered Markdown, LaTeX source, build log, and compiled PDF. Poll only while draft/review/compile actions are running.

- [ ] **Step 4: Run full verification**

Run: `python -m pytest backend/tests -q`

Expected: all backend tests pass.

Run: `Set-Location frontend; npm test -- --run; npm run build`

Expected: all frontend tests and build pass.

- [ ] **Step 5: Commit paper API and UI**

```powershell
git add backend/api/modeling.py backend/tests/test_paper_api.py frontend/src/services/api.ts frontend/src/services/api.test.ts frontend/src/components/PaperWorkspace.tsx frontend/src/components/PaperWorkspace.test.tsx frontend/src/components/ReviewIssuesPanel.tsx frontend/src/components/ReviewIssuesPanel.test.tsx frontend/src/components/FinalPaperApprovalCard.tsx frontend/src/components/FinalPaperApprovalCard.test.tsx frontend/src/views/ModelingProjectsView.tsx
git commit -m "feat: add traceable paper review workbench"
```

### Task 6: Phase 4 Traceability Checkpoint

**Files:**
- No source changes expected.

**Interfaces:**
- Verifies paper facts, review blocking, approval invalidation, and compilation.

- [ ] **Step 1: Generate a paper from completed experiments**

Expected: editable sources contain placeholders and no literal measured metric values.

- [ ] **Step 2: Delete one referenced artifact and run review**

Expected: review produces a blocking issue and final approval remains disabled.

- [ ] **Step 3: Restore the artifact, pass review, and approve the exact paper hash**

Expected: approval payload lists Markdown, LaTeX, bibliography, claims, and review hash.

- [ ] **Step 4: Compile PDF and inspect claims**

Expected: `deliverables/paper.pdf` exists; every rendered number and figure path has one `paper_claims` row.

- [ ] **Step 5: Modify Markdown after approval**

Expected: compilation is rejected until a new review and final approval complete.
