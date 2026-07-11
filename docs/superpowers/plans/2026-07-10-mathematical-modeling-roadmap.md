# Mathematical Modeling Workflow Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the approved mathematical-modeling workflow as six independently testable phases, ending with a reproducible paper PDF and an approval-gated Git commit.

**Architecture:** Keep the existing React/FastAPI application and add a bounded `modeling` domain. SQLite stores workflow metadata while each competition owns a separate filesystem workspace and Git repository; every later phase consumes the typed services and artifact contracts established by earlier phases.

**Tech Stack:** Python 3.10+, FastAPI 0.104.1, Pydantic 2.5.0, SQLite, React 18, TypeScript 5.2, Zustand 4.4, Vitest 1.6, pytest/unittest, local Git, XeLaTeX.

**Goal-mode execution:** Use `docs/superpowers/execution/2026-07-11-mathematical-modeling-goal-loop.md` for one-phase-per-Goal execution and `docs/superpowers/execution/2026-07-11-mathematical-modeling-goal-progress.md` for cross-session recovery.

## Global Constraints

- The first release supports data-driven modeling only: cleaning, statistics, prediction, classification, evaluation, and visualization.
- Keep React + TypeScript + Vite + TailwindCSS + Zustand on the frontend and FastAPI + SQLite on the backend.
- Each competition uses a separate workspace and separate Git repository; never initialize a project inside the NotebookLM source tree.
- `problem/original` and `data/raw` are immutable after import; completed `experiments/exp-*` directories are append-only.
- Four approvals are mandatory: model plan, experiment execution, final paper, and Git commit.
- An approval is valid only for its recorded SHA-256 content hash.
- Markdown is the editable paper draft; LaTeX is the formal source; XeLaTeX produces the PDF with shell escape disabled.
- Agents exchange structured artifacts, not unbounded chat; one stage permits at most three automatic rework attempts.
- Generated code runs only through registered tools, inside the project workspace, with scrubbed secrets, no implicit network, a timeout, and process-tree termination.
- Git automation permits only status, diff, explicit-path add, and approval-gated commit; it never pushes or runs reset, clean, rebase, branch deletion, or remote mutation.
- Preserve all unrelated dirty-worktree changes. Stage and commit only the files named by the active task.

---

## Plan Set

1. [Phase 1 — Project Foundation](2026-07-10-mathematical-modeling-phase1-foundation.md)
   - Adds the modeling state machine, SQLite store, safe workspace creation, project API, and first frontend module.
   - Exit: a project can be created, listed, opened, advanced through simulated legal states, rolled back, and recovered after restart.
2. [Phase 2 — Problem, Data, and Model Approval](2026-07-10-mathematical-modeling-phase2-intake-planning.md)
   - Adds immutable input import, problem/data contracts, CSV profiling, structured problem/model agents, artifacts, and plan approval.
   - Exit: a real prompt and CSV produce an inspectable, approval-bound model plan.
3. [Phase 3 — Experiment Execution](2026-07-10-mathematical-modeling-phase3-experiments.md)
   - Adds code generation contracts, execution tickets, a restricted Python runner, immutable experiment records, metrics, and figures.
   - Exit: an approved baseline and candidate model run reproducibly and produce indexed artifacts.
4. [Phase 4 — Paper and Review](2026-07-10-mathematical-modeling-phase4-paper.md)
   - Adds metric/figure placeholders, Markdown and LaTeX generation, independent review, final approval, compilation, and PDF preview.
   - Exit: a paper compiled from traceable experiment facts passes review.
5. [Phase 5 — Delivery and Git](2026-07-10-mathematical-modeling-phase5-delivery-git.md)
   - Adds the delivery manifest, reproducibility checks, archive output, Git policy scanning, diff review, and commit approval.
   - Exit: the independent project repository receives one safe, user-approved commit.
6. [Phase 6 — Recovery and End-to-End Hardening](2026-07-10-mathematical-modeling-phase6-hardening.md)
   - Adds interrupted-run recovery, resource hardening, runtime health, a fixed regression competition, and full E2E coverage.
   - Exit: the workflow survives restart and repeatedly completes the fixture competition without untraceable facts or unsafe writes.

## Stable Cross-Phase Interfaces

These names are fixed across all six plans:

```text
WorkflowState contains exactly: project_initialized, problem_parsing,
data_profiling, model_planning, model_approval_pending,
experiment_implementation, execution_approval_pending, experiment_running,
result_validation, paper_drafting, consistency_review,
final_approval_pending, packaging, commit_approval_pending, committing,
completed.

ModelingProjectService.create_project(name: str,
deadline: str | None = None) -> dict
ModelingProjectService.list_projects() -> list[dict]
ModelingProjectService.get_project(project_id: str) -> dict | None
ModelingProjectService.advance(project_id: str) -> dict
ModelingProjectService.rollback(project_id: str, reason: str) -> dict
ModelingProjectService.list_tasks(project_id: str) -> list[dict]
ModelingProjectService.list_runs(project_id: str) -> list[dict]

ArtifactService.register(project_id: str, artifact_type: str,
relative_path: str, source_run_id: str | None = None,
source_experiment_id: str | None = None) -> dict
ArtifactService.resolve(project_id: str, artifact_id: str) -> dict

ApprovalService.request(project_id: str, gate: str, payload: dict) -> dict
ApprovalService.decide(approval_id: str, decision: str, payload_hash: str,
comment: str = "") -> dict
ApprovalService.require_approved(project_id: str, gate: str,
payload_hash: str) -> dict
```

TypeScript consumes snake_case JSON without a second normalization layer for the modeling domain.

## Phase Gates

- [x] **Gate 1:** Run all Phase 1 backend tests, frontend tests, and `npm run build`; commit only after project persistence and navigation work together.
- [x] **Gate 2:** Complete one real CSV intake and approve a content-hashed model plan; verify raw files remain unchanged.
- [ ] **Gate 3:** Re-run a recorded experiment and compare metrics within the declared tolerance; verify a changed command invalidates approval.
- [ ] **Gate 4:** Compile `paper/main.tex` and prove every metric/figure placeholder resolves to a registered artifact.
- [ ] **Gate 5:** Scan the exact staged file list and create a commit only after matching approval; verify no remote operation occurs.
- [ ] **Gate 6:** Interrupt the fixture workflow mid-run, restart the app, recover, and finish the same project.

## Approved-Spec Coverage

| Design requirement | Owning plan and tasks |
| --- | --- |
| State machine, independent workspace, project API | Phase 1, Tasks 1–4 |
| Three-column modeling module and project persistence | Phase 1, Tasks 5–6 |
| Immutable prompt/data import and manifests | Phase 2, Task 2 |
| Artifact index and hash-bound approvals | Phase 2, Task 1 |
| Problem parsing, data profile, up to three model candidates | Phase 2, Tasks 3–4 |
| Model approval UI and workflow gate | Phase 2, Tasks 4–6 |
| Generated code, virtual environment, dependency command, execution ticket | Phase 3, Tasks 2–3 |
| Timeout, output cap, network denial, secret scrubbing, process-tree kill | Phase 3, Task 4 and Phase 6, Task 3 |
| Immutable experiments, metrics, figures, environment, reproducibility | Phase 3, Tasks 1, 4–6 |
| Markdown, LaTeX, claim provenance, reviewer, final approval, PDF | Phase 4, Tasks 1–6 |
| Delivery manifest, restricted data policy, code archive, Outputs link | Phase 5, Tasks 1–2 |
| Secret/size/path Git scan, explicit add, diff, approval-gated commit | Phase 5, Tasks 3–6 |
| Restart recovery, runtime readiness, fixed competition E2E | Phase 6, Tasks 1–7 |

No approved design section is deferred outside this plan set. Docker/system-level isolation, model-family expansion, concurrent experiment branches, and Git push remain explicit non-goals.

## Repository-Wide Verification

Run from the repository root after each phase:

```powershell
python -m pytest backend/tests -q
Set-Location frontend
npm test -- --run
npm run build
```

Expected: backend tests pass, Vitest exits with zero failures, and Vite emits a production build without TypeScript errors.
