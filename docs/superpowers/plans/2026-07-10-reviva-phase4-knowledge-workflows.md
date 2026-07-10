# Reviva Phase 4 Knowledge Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Reviva-like knowledge workflows: wiki context binding, document/wiki/note/output preview, generated task progress cards, and a durable artifact lifecycle for reusable study outputs.

**Architecture:** Build on existing SQLite metadata, wiki, outputs, notes, and agent-run persistence. Add missing preview APIs and lightweight task/artifact lifecycle fields where necessary. The UI remains a local-first workbench; generated artifacts stay inspectable and recoverable.

**Tech Stack:** FastAPI, Python, SQLite, React 18, TypeScript, Zustand, Tailwind CSS, React Markdown, Vitest, React Testing Library, Playwright screenshots.

## Global Constraints

- Do not copy Reviva source code.
- Do not add Electron-only filesystem features.
- Do not expose API keys or local absolute file paths unnecessarily in frontend responses.
- Previews must be bounded and safe: text snippets or structured metadata only unless an existing backend route intentionally returns content.
- Generated tasks must be persisted or derivable from persisted agent runs/outputs before they count as complete.
- Use TDD for backend persistence/API and frontend behavior.

---

## File Structure

- Modify: `backend/services/document_metadata_store.py` for optional artifact lifecycle/task fields if not already present.
- Modify or create: `backend/api/preview.py` if a consolidated preview endpoint is needed.
- Modify: `backend/main.py` to register preview route if created.
- Create or modify: `backend/tests/test_preview_api.py`.
- Modify: `frontend/src/services/api.ts` for preview and artifact lifecycle wrappers.
- Create: `frontend/src/components/PreviewPane.tsx` and `frontend/src/components/PreviewPane.test.tsx`.
- Create: `frontend/src/components/TaskProgressCards.tsx` and `frontend/src/components/TaskProgressCards.test.tsx`.
- Create: `frontend/src/components/ArtifactLifecycleMenu.tsx` and `frontend/src/components/ArtifactLifecycleMenu.test.tsx`.
- Modify: `frontend/src/components/RightInspector.tsx` and `frontend/src/components/RightInspector.test.tsx`.
- Modify: `frontend/src/components/WorkbenchContextPanel.tsx` for stronger wiki binding if Phase 2 kept it minimal.
- Modify: `frontend/src/views/WikiView.tsx`, `frontend/src/views/OutputsView.tsx`, `frontend/src/views/NotesView.tsx` only for navigation into preview/lifecycle.

## Task 1: Preview Data Contract

**Files:**
- Modify: `frontend/src/services/api.ts`
- Create: `backend/api/preview.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_preview_api.py`

**Interfaces:**
- Produces endpoint: `GET /api/preview/{target_type}/{target_id}`
- `target_type`: `document | wiki | note | output`
- Produces response: `{ type: string; id: string; title: string; content_preview: string; metadata: Record<string, unknown>; links: Array<{ type: string; id: string; title: string }> }`
- Produces frontend wrapper: `previewApi.get(targetType, targetId): Promise<PreviewItem>`

- [ ] **Step 1: Write failing backend tests**

Use fake/in-memory services or temporary SQLite data and assert:

- Document preview returns filename, status, chunk count, summary if available.
- Wiki preview returns title/content preview/source links.
- Note preview returns title/content preview/links.
- Output preview returns title/kind/content preview/source links.
- Missing target returns 404.

- [ ] **Step 2: Run failing tests**

Run:

```powershell
cd backend
$env:PYTHONPATH='D:\develop\python\NotebookLM\backend;D:\develop\python\NotebookLM\backend\venv\Lib\site-packages'
python -m pytest tests\test_preview_api.py -q
```

Expected: FAIL until route exists.

- [ ] **Step 3: Implement preview route**

Use existing metadata store/service methods. Cap `content_preview` at 4000 characters.

- [ ] **Step 4: Add frontend API wrapper and tests**

Add `previewApi` to `frontend/src/services/api.ts`; extend `api.test.ts`.

- [ ] **Step 5: Verify focused tests**

Run backend preview tests and frontend API tests.

Expected: PASS.

## Task 2: Preview Pane

**Files:**
- Create: `frontend/src/components/PreviewPane.tsx`
- Create: `frontend/src/components/PreviewPane.test.tsx`
- Modify: `frontend/src/components/RightInspector.tsx`

**Interfaces:**
- Consumes: `previewTarget`
- Calls: `previewApi.get(previewTarget.type, previewTarget.id)`
- Produces: `data-testid="preview-pane"`
- Produces states: empty, loading, error, loaded

- [ ] **Step 1: Write failing tests**

Assert:

- Empty state renders `Select an item to preview`.
- Loading state renders without layout jump.
- Loaded state renders title, metadata, markdown/text preview, and links.
- Error state offers retry.
- Long content is scrollable and does not overflow the panel.

- [ ] **Step 2: Run failing tests**

```powershell
cd frontend
npm.cmd test -- PreviewPane.test.tsx RightInspector.test.tsx --run
```

Expected: FAIL until PreviewPane exists.

- [ ] **Step 3: Implement pane**

Use neutral paper surface and compact metadata rows. Do not render raw HTML.

- [ ] **Step 4: Wire into RightInspector Preview tab**

Replace placeholder preview from Phase 2 with `PreviewPane`.

- [ ] **Step 5: Verify focused tests**

Run focused tests again.

Expected: PASS.

## Task 3: Wiki Context Binding Upgrade

**Files:**
- Modify: `frontend/src/components/WorkbenchContextPanel.tsx`
- Modify: `frontend/src/components/WorkbenchContextPanel.test.tsx`
- Modify: `frontend/src/components/ContextPillBar.tsx`
- Modify: `frontend/src/components/ContextPillBar.test.tsx`
- Modify: `frontend/src/components/ChatInterface.tsx`

**Interfaces:**
- Consumes: `wikiApi.list()`, `selectedWikiPageIds`, `toggleWikiContext`
- Produces visible selected wiki context in composer
- Chat request remains backward-compatible; if backend does not accept wiki IDs yet, include wiki context as local prompt preface only after a backend contract is added in a separate test.

- [ ] **Step 1: Write failing tests**

Assert:

- KB tab lists wiki pages with checkboxes/toggles.
- Selected wiki pages appear as context pills.
- Toggling wiki context updates store.
- Selected wiki context remains visible when switching left-panel tabs.

- [ ] **Step 2: Run failing tests**

```powershell
cd frontend
npm.cmd test -- WorkbenchContextPanel.test.tsx ContextPillBar.test.tsx --run
```

Expected: FAIL until upgraded.

- [ ] **Step 3: Implement binding**

Keep source and wiki pills visually distinct but neutral.

- [ ] **Step 4: Verify focused tests**

Expected: PASS.

## Task 4: Generated Task Progress Cards

**Files:**
- Create: `frontend/src/components/TaskProgressCards.tsx`
- Create: `frontend/src/components/TaskProgressCards.test.tsx`
- Modify: `frontend/src/components/RightInspector.tsx`
- Modify: `frontend/src/services/api.ts` if an agent run status filter is needed

**Interfaces:**
- Consumes: `agentsApi.listRuns()`
- Produces cards for running/completed/failed runs
- Produces actions: `Open artifact`, `View run`

- [ ] **Step 1: Write failing tests**

Mock agent runs and assert:

- Running task shows spinner/progress status.
- Completed task with `output_id` shows `Open artifact`.
- Failed task shows error summary.
- Clicking `Open artifact` sets output preview target.
- Cards use neutral surface and compact status dots.

- [ ] **Step 2: Run failing tests**

```powershell
cd frontend
npm.cmd test -- TaskProgressCards.test.tsx --run
```

Expected: FAIL until component exists.

- [ ] **Step 3: Implement cards**

Poll or refresh manually; do not create unbounded intervals. If polling is used, clean it up in `useEffect`.

- [ ] **Step 4: Verify focused tests**

Expected: PASS.

## Task 5: Artifact Lifecycle

**Files:**
- Modify: `backend/services/document_metadata_store.py`
- Modify: `backend/services/output_service.py`
- Modify: `backend/api/outputs.py`
- Create or modify: `backend/tests/test_output_export.py`
- Create: `frontend/src/components/ArtifactLifecycleMenu.tsx`
- Create: `frontend/src/components/ArtifactLifecycleMenu.test.tsx`
- Modify: `frontend/src/components/ArtifactList.tsx`
- Modify: `frontend/src/views/OutputsView.tsx`

**Interfaces:**
- Backend optional fields: `status: 'active' | 'archived' | 'deleted'`, `deleted_at: string | null`
- Produces endpoint: `POST /api/outputs/{output_id}/archive`
- Produces endpoint: `POST /api/outputs/{output_id}/restore`
- Existing delete may remain hard delete unless this task explicitly changes it to soft delete with tests.

- [ ] **Step 1: Write failing backend tests**

Assert:

- Archive hides output from default list but `include_archived=true` shows it.
- Restore makes archived output visible again.
- Export still works for archived output if explicitly loaded.

- [ ] **Step 2: Run failing backend tests**

Expected: FAIL until lifecycle exists.

- [ ] **Step 3: Implement lifecycle backend**

Prefer soft archive over recycle bin unless product owner explicitly asks for full recycle bin.

- [ ] **Step 4: Write failing frontend tests**

Assert:

- Artifact menu shows `Preview`, `Export`, `Archive`.
- Archive action calls API and refreshes list.
- Archived filter in OutputsView can reveal archived items.

- [ ] **Step 5: Implement frontend lifecycle UI**

Use a small icon/menu button, not a large text block.

- [ ] **Step 6: Verify focused tests**

Run backend output tests and frontend artifact tests.

Expected: PASS.

## Task 6: Full Phase Verification

- [ ] **Step 1: Backend tests**

```powershell
cd backend
$env:PYTHONPATH='D:\develop\python\NotebookLM\backend;D:\develop\python\NotebookLM\backend\venv\Lib\site-packages'
python -m pytest tests\test_preview_api.py tests\test_output_export.py tests\test_agent_service.py tests\test_wiki_api.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Frontend tests**

```powershell
cd frontend
npm.cmd test -- --run
```

Expected: all frontend tests pass.

- [ ] **Step 3: Build**

```powershell
cd frontend
npm.cmd run build
```

Expected: TypeScript and Vite build exit 0.

- [ ] **Step 4: Screenshot verify**

Capture 1440 and 390 viewports.

Expected visual result:

- Right Preview tab can show document/wiki/note/output previews.
- KB context binding is visible in left panel and composer pills.
- Task cards show running/completed/failed states without overlap.
- Artifact lifecycle menu is compact and keyboard reachable.
- Mobile viewport has no clipped composer, preview content, or menu text.
