# Reviva-Inspired Phase 1 Shell Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Keep commits small and verify after each working slice.

**Goal:** Transform the current React/FastAPI NotebookLM interface into a Reviva-inspired knowledge workbench shell while keeping the existing Python backend, RAG flow, settings policy, and document persistence.

**Architecture:** Frontend reorganizes around module views and a persistent app shell. Backend changes should be minimal in Phase 1 unless an endpoint contract blocks the shell. Existing API routes remain stable.

**Primary Constraints:**

1. Do not copy Reviva source code.
2. Do not switch to Electron/Vue.
3. Do not add API key inputs to the UI.
4. Do not break upload, chat streaming, citations, notes, or settings status.
5. Keep all frontend API calls in `frontend/src/services/api.ts`.

## Target File Areas

Expected frontend areas:

1. `frontend/src/App.tsx`
2. `frontend/src/components/Sidebar.tsx`
3. `frontend/src/components/ChatInterface.tsx`
4. `frontend/src/components/SettingsModal.tsx`
5. `frontend/src/components/UploadModal.tsx`
6. `frontend/src/components/NotesModal.tsx`
7. `frontend/src/services/api.ts`
8. `frontend/src/store/useStore.ts`

New frontend areas may include:

1. `frontend/src/layouts/WorkbenchShell.tsx`
2. `frontend/src/views/DashboardView.tsx`
3. `frontend/src/views/WorkbenchView.tsx`
4. `frontend/src/views/SourcesView.tsx`
5. `frontend/src/views/NotesView.tsx`
6. `frontend/src/views/OutputsView.tsx`
7. `frontend/src/views/SettingsView.tsx`
8. `frontend/src/components/RightInspector.tsx`
9. `frontend/src/components/ModuleNav.tsx`

Backend should not need new files in this phase unless verification exposes a missing status or citation contract.

## Module Shell Design

The first screen should be the workbench, not a landing page.

Layout:

1. Left module rail: Dashboard, Workbench, Sources, Notes, Outputs, Settings.
2. Left content panel: source list or active module navigation.
3. Center workspace: chat, dashboard, source management, notes, or outputs.
4. Right inspector: citations, retrieval hits, note links, or runtime status.
5. Top toolbar: workspace title, active mode, model status, upload, search, settings.

Visual direction:

1. Dense and calm.
2. 8px or smaller card radii.
3. Avoid decorative hero sections.
4. Use icons for navigation and tool buttons.
5. Keep text inside buttons and panels from wrapping awkwardly.

## Phase Tasks

### Task 1: Audit Current UI Composition

**Files:**

1. Read `frontend/src/App.tsx`
2. Read major components in `frontend/src/components`
3. Read `frontend/src/store/useStore.ts`

**Checklist:**

- [ ] Identify which state is global and which state is component-local.
- [ ] Confirm current upload, chat, notes, settings, and document list paths.
- [ ] Identify hardcoded layout assumptions that block a module shell.
- [ ] Record any backend API gaps before editing.

**Expected result:** A short implementation note in the coding session, not necessarily a committed file.

### Task 2: Add App-Level Module State

**Files:**

1. Modify `frontend/src/store/useStore.ts` or local `App.tsx` state.

**Checklist:**

- [ ] Add a typed module key: `dashboard`, `workbench`, `sources`, `notes`, `outputs`, `settings`.
- [ ] Default to `workbench`.
- [ ] Keep settings modal behavior available if the Settings view is not complete yet.
- [ ] Avoid storing secrets or provider credentials.

**Verification:**

- [ ] `npm run build`

**Commit:**

```bash
git add frontend/src/store/useStore.ts frontend/src/App.tsx
git commit -m "feat: add workbench module state"
```

### Task 3: Create Shell Layout

**Files:**

1. Create `frontend/src/layouts/WorkbenchShell.tsx`
2. Create `frontend/src/components/ModuleNav.tsx`
3. Modify `frontend/src/App.tsx`

**Checklist:**

- [ ] Add persistent left module rail.
- [ ] Add top toolbar region.
- [ ] Add left panel, center panel, and right inspector slots.
- [ ] Keep existing upload/settings buttons accessible.
- [ ] Keep responsive behavior usable on narrower screens.

**Verification:**

- [ ] `npm run build`

**Commit:**

```bash
git add frontend/src/layouts/WorkbenchShell.tsx frontend/src/components/ModuleNav.tsx frontend/src/App.tsx
git commit -m "feat: add reviva-inspired workbench shell"
```

### Task 4: Move Existing Chat Into Workbench View

**Files:**

1. Create `frontend/src/views/WorkbenchView.tsx`
2. Modify `frontend/src/App.tsx`
3. Modify `frontend/src/components/ChatInterface.tsx` only if needed for layout props.

**Checklist:**

- [ ] Render current chat in the center workspace.
- [ ] Render source selection in the left panel.
- [ ] Render citations or empty inspector state in the right panel.
- [ ] Preserve streaming behavior.
- [ ] Preserve selected document behavior.

**Verification:**

- [ ] `npm run build`
- [ ] Manual smoke test: ask one question against an existing source if backend is running.

**Commit:**

```bash
git add frontend/src/views/WorkbenchView.tsx frontend/src/App.tsx frontend/src/components/ChatInterface.tsx
git commit -m "feat: move chat into workbench view"
```

### Task 5: Add Dashboard And Sources Views

**Files:**

1. Create `frontend/src/views/DashboardView.tsx`
2. Create `frontend/src/views/SourcesView.tsx`
3. Modify `frontend/src/App.tsx`

**Checklist:**

- [ ] Dashboard shows document count, configured model status, recent source states, and quick actions.
- [ ] Sources view shows document list, upload entry, processing status, and delete action.
- [ ] Reuse existing document APIs.
- [ ] Do not duplicate source state across incompatible stores.

**Verification:**

- [ ] `npm run build`

**Commit:**

```bash
git add frontend/src/views/DashboardView.tsx frontend/src/views/SourcesView.tsx frontend/src/App.tsx
git commit -m "feat: add dashboard and sources views"
```

### Task 6: Add Notes, Outputs, And Settings Views

**Files:**

1. Create `frontend/src/views/NotesView.tsx`
2. Create `frontend/src/views/OutputsView.tsx`
3. Create `frontend/src/views/SettingsView.tsx`
4. Modify `frontend/src/App.tsx`

**Checklist:**

- [ ] Notes view reuses existing notes API and note modal logic where practical.
- [ ] Outputs view starts as a real empty-state plus roadmap actions, not fake generated content.
- [ ] Settings view reuses safe settings status and test LLM behavior.
- [ ] Settings view never renders an API key input.

**Verification:**

- [ ] `npm run build`

**Commit:**

```bash
git add frontend/src/views/NotesView.tsx frontend/src/views/OutputsView.tsx frontend/src/views/SettingsView.tsx frontend/src/App.tsx
git commit -m "feat: add notes outputs and settings views"
```

### Task 7: Right Inspector Foundation

**Files:**

1. Create `frontend/src/components/RightInspector.tsx`
2. Modify `frontend/src/views/WorkbenchView.tsx`
3. Modify `frontend/src/components/ChatInterface.tsx` if citation state needs to be lifted.

**Checklist:**

- [ ] Inspector supports tabs or modes: Citations, Notes, Runtime.
- [ ] Citations show source title, page/section when available, and snippet.
- [ ] Runtime shows provider/model/config status without secrets.
- [ ] Empty states are useful and compact.

**Verification:**

- [ ] `npm run build`

**Commit:**

```bash
git add frontend/src/components/RightInspector.tsx frontend/src/views/WorkbenchView.tsx frontend/src/components/ChatInterface.tsx
git commit -m "feat: add workbench right inspector"
```

### Task 8: Final Verification

**Checklist:**

- [ ] Run frontend build:

```bash
cd frontend
npm run build
```

- [ ] Run backend unit tests:

```bash
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

- [ ] Run backend compile check:

```bash
cd backend
$env:DEBUG='false'
$files = Get-ChildItem -Recurse -Include *.py | Where-Object { $_.FullName -notmatch '\\venv\\' } | ForEach-Object { $_.FullName }
.\venv\Scripts\python.exe -m py_compile @files
```

- [ ] Smoke test in browser if dev server is available:

1. Open app.
2. Confirm workbench shell renders.
3. Upload or select a source.
4. Ask a streaming question.
5. Open settings and run LLM test.

**Commit if final fixes were needed:**

```bash
git add <changed-files>
git commit -m "fix: polish workbench shell verification issues"
```

## Done Criteria

Phase 1 is complete when:

1. UI has a Reviva-inspired module shell.
2. Existing RAG/chat/upload/settings features still work.
3. API key remains backend-only.
4. Frontend build passes.
5. Backend tests and compile checks pass.
6. The branch is pushed to GitHub.

