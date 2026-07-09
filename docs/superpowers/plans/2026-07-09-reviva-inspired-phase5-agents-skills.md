# Reviva-Inspired Phase 5 Agents Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal, inspectable Agents and Skills system after the core workbench, retrieval, notes, Wiki, and outputs are stable.

**Architecture:** Implement a small local skill manifest format, a backend tool registry, and explicit agent run records. Avoid hidden autonomous execution; every run must expose steps, tool calls, status, and outputs.

**Tech Stack:** FastAPI, Python, Pydantic, SQLite, React 18, TypeScript, lucide-react, existing `LLMService`.

## Global Constraints

- Do not copy Reviva source code.
- Do not execute arbitrary shell commands from skills.
- Do not expose API keys to the frontend.
- Agent runs must be inspectable and recoverable.
- Skills may only call registered backend tools.
- Commit after each independently working task.

---

## File Structure

- Create: `backend/services/skill_service.py`
- Create: `backend/services/tool_registry.py`
- Create: `backend/services/agent_service.py`
- Create: `backend/api/skills.py`
- Create: `backend/api/agents.py`
- Modify: `backend/services/document_metadata_store.py`
- Modify: `backend/main.py`
- Create: `backend/skills/paper_planner/skill.json`
- Create: `backend/skills/course_reviewer/skill.json`
- Create: `backend/skills/kb_maintainer/skill.json`
- Modify: `frontend/src/store/useStore.ts`
- Modify: `frontend/src/components/ModuleNav.tsx`
- Create: `frontend/src/views/SkillsView.tsx`
- Create: `frontend/src/views/AgentsView.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/services/api.ts`

## Task 1: Skill Manifest Loader

**Files:**

- Create: `backend/services/skill_service.py`
- Create: `backend/tests/test_skill_service.py`
- Create: `backend/skills/paper_planner/skill.json`
- Create: `backend/skills/course_reviewer/skill.json`
- Create: `backend/skills/kb_maintainer/skill.json`

**Interfaces:**

- Produces: `SkillService.list_skills() -> list[dict]`
- Produces: `SkillService.get_skill(skill_id: str) -> Optional[dict]`
- Produces manifest fields: `skill_id`, `name`, `description`, `allowed_tools`, `prompt_template`, `output_kind`

- [ ] **Step 1: Add failing tests**

Test that:

1. Built-in skill manifests load.
2. Missing required fields raise `ValueError`.
3. A skill can only reference known tool names after Task 2.

- [ ] **Step 2: Create manifest format**

Example `backend/skills/paper_planner/skill.json`:

```json
{
  "skill_id": "paper_planner",
  "name": "Paper Planner",
  "description": "Create a paper outline with claims, evidence, and citation anchors.",
  "allowed_tools": ["retrieve_sources", "create_output"],
  "prompt_template": "Use selected sources to create a paper plan with claims, evidence, counterpoints, and citation anchors.",
  "output_kind": "paper_plan"
}
```

- [ ] **Step 3: Implement SkillService**

Load JSON files from `backend/skills/*/skill.json` and validate required fields.

- [ ] **Step 4: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_skill_service -v
```

```powershell
git add backend/services/skill_service.py backend/tests/test_skill_service.py backend/skills/paper_planner/skill.json backend/skills/course_reviewer/skill.json backend/skills/kb_maintainer/skill.json
git commit -m "feat: add skill manifest loader"
```

## Task 2: Safe Tool Registry

**Files:**

- Create: `backend/services/tool_registry.py`
- Create: `backend/tests/test_tool_registry.py`

**Interfaces:**

- Produces: `ToolRegistry.list_tools() -> list[dict]`
- Produces: `ToolRegistry.run_tool(tool_name: str, params: dict) -> dict`
- Registered tools: `retrieve_sources`, `create_note`, `create_output`, `create_wiki_page`

- [ ] **Step 1: Add failing tests**

Assert:

1. Unknown tool names are rejected.
2. Tool schemas are listed without secrets.
3. Tool calls return structured success or error dictionaries.

- [ ] **Step 2: Implement registry**

Registry maps tool names to Python callables. It does not accept shell commands or arbitrary import paths.

- [ ] **Step 3: Wire existing services**

Use existing retrieval, note, output, and Wiki services.

- [ ] **Step 4: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_tool_registry -v
```

```powershell
git add backend/services/tool_registry.py backend/tests/test_tool_registry.py
git commit -m "feat: add safe tool registry"
```

## Task 3: Agent Run Persistence

**Files:**

- Modify: `backend/services/document_metadata_store.py`
- Create: `backend/tests/test_agent_store.py`

**Interfaces:**

- Produces: `create_agent_run(skill_id: str, input_payload: dict) -> dict`
- Produces: `append_agent_step(run_id: str, step: dict) -> None`
- Produces: `update_agent_run_status(run_id: str, status: str, output_id: str | None = None, error: str | None = None) -> None`
- Produces: `get_agent_run(run_id: str) -> Optional[dict]`
- Produces: `list_agent_runs() -> list[dict]`

- [ ] **Step 1: Add failing tests**

Test create, append step, mark complete, reopen DB, and list run.

- [ ] **Step 2: Add SQLite tables**

Add:

```sql
CREATE TABLE IF NOT EXISTS agent_runs (
  run_id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL,
  status TEXT NOT NULL,
  input_payload_json TEXT NOT NULL,
  output_id TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_steps (
  step_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  step_index INTEGER NOT NULL,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES agent_runs(run_id) ON DELETE CASCADE
);
```

- [ ] **Step 3: Implement store methods**

Return run dictionaries with `steps` ordered by `step_index`.

- [ ] **Step 4: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_agent_store -v
```

```powershell
git add backend/services/document_metadata_store.py backend/tests/test_agent_store.py
git commit -m "feat: persist agent runs"
```

## Task 4: Agent Service And APIs

**Files:**

- Create: `backend/services/agent_service.py`
- Create: `backend/api/skills.py`
- Create: `backend/api/agents.py`
- Modify: `backend/main.py`
- Modify: `frontend/src/services/api.ts`

**Interfaces:**

- Produces: `GET /api/skills`
- Produces: `GET /api/skills/{skill_id}`
- Produces: `GET /api/agents/runs`
- Produces: `POST /api/agents/runs`
- Produces: `GET /api/agents/runs/{run_id}`

- [ ] **Step 1: Implement AgentService**

Execution flow:

1. Create run with status `running`.
2. Retrieve selected sources.
3. Build prompt from skill manifest.
4. Generate content with `LLMService`.
5. Create output using `OutputService`.
6. Mark run `completed`.
7. On failure, append error step and mark run `failed`.

- [ ] **Step 2: Add APIs**

Expose skill list and agent run endpoints. Do not stream agent steps in this phase; frontend polls run detail.

- [ ] **Step 3: Add frontend API methods**

Add `skillsApi` and `agentsApi` to `frontend/src/services/api.ts`.

- [ ] **Step 4: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m py_compile services/agent_service.py api/skills.py api/agents.py main.py
```

```powershell
cd frontend
npm run build
```

```powershell
git add backend/services/agent_service.py backend/api/skills.py backend/api/agents.py backend/main.py frontend/src/services/api.ts
git commit -m "feat: add agent and skill apis"
```

## Task 5: Agents And Skills UI

**Files:**

- Modify: `frontend/src/store/useStore.ts`
- Modify: `frontend/src/components/ModuleNav.tsx`
- Create: `frontend/src/views/SkillsView.tsx`
- Create: `frontend/src/views/AgentsView.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**

- Produces app modules: `skills`, `agents`
- Consumes: `skillsApi.list()`, `agentsApi.createRun()`, `agentsApi.getRun()`, `agentsApi.listRuns()`

- [ ] **Step 1: Add modules**

Extend `AppModule` with `skills` and `agents`. Add icons to `ModuleNav`.

- [ ] **Step 2: Create SkillsView**

Show built-in skills, allowed tools, output kind, and a run button.

- [ ] **Step 3: Create AgentsView**

Show run list, status, steps, error state, and output link.

- [ ] **Step 4: Add polling**

When a run is started, poll `GET /api/agents/runs/{run_id}` every 1500ms until status is `completed` or `failed`.

- [ ] **Step 5: Verify and commit**

```powershell
cd frontend
npm run build
```

```powershell
git add frontend/src/store/useStore.ts frontend/src/components/ModuleNav.tsx frontend/src/views/SkillsView.tsx frontend/src/views/AgentsView.tsx frontend/src/App.tsx
git commit -m "feat: add agents and skills UI"
```

## Task 6: Phase Verification

- [ ] **Step 1: Run global verification commands from the roadmap index**

- [ ] **Step 2: Manual acceptance**

Confirm:

1. Skills list renders without secrets.
2. Paper Planner run creates a persisted output.
3. Course Reviewer run creates review-oriented output.
4. Failed run shows visible error state.
5. Agent steps are inspectable after backend restart.

- [ ] **Step 3: Push**

```powershell
git status -sb
git push
```

## Done Criteria

Phase 5 is complete when:

1. Skill manifests load and validate.
2. Registered tools are explicit and safe.
3. Agent runs are persisted with visible steps.
4. Skills can create outputs from selected local sources.
5. The frontend has usable Agents and Skills modules.
6. Global verification commands pass.

