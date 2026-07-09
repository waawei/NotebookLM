# Reviva-Inspired Phase 4 Notes Wiki Outputs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn chat answers and source material into reusable notes, Wiki pages, and generated outputs.

**Architecture:** Add durable SQLite-backed artifact services. Keep generation behind backend APIs and render artifacts in the existing React workbench modules.

**Tech Stack:** FastAPI, Python stdlib `sqlite3`, Pydantic, React 18, TypeScript, React Markdown, lucide-react.

## Global Constraints

- Do not copy Reviva source code.
- Do not expose API keys to the frontend.
- Keep notes, Wiki, and outputs grounded in local sources.
- Keep generated artifacts persisted in SQLite.
- Keep all frontend API calls in `frontend/src/services/api.ts`.
- Commit after each independently working task.

---

## File Structure

- Modify: `backend/services/document_metadata_store.py` for notes links, Wiki pages, and outputs.
- Modify: `backend/services/note_service.py` to use SQLite and source/message links.
- Create: `backend/services/wiki_service.py`
- Create: `backend/services/output_service.py`
- Create: `backend/api/wiki.py`
- Create: `backend/api/outputs.py`
- Modify: `backend/main.py`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/views/NotesView.tsx`
- Create: `frontend/src/views/WikiView.tsx`
- Modify: `frontend/src/views/OutputsView.tsx`
- Modify: `frontend/src/components/ModuleNav.tsx`
- Modify: `frontend/src/store/useStore.ts`

## Task 1: SQLite Artifact Schema

**Files:**

- Modify: `backend/services/document_metadata_store.py`
- Create: `backend/tests/test_artifact_store.py`

**Interfaces:**

- Produces: `save_note_link(note_id: str, source_type: str, source_id: str) -> None`
- Produces: `create_wiki_page(title: str, content: str, source_doc_ids: list[str]) -> dict`
- Produces: `update_wiki_page(page_id: str, title: str, content: str) -> bool`
- Produces: `create_output(kind: str, title: str, content: str, source_doc_ids: list[str]) -> dict`
- Produces: `list_outputs(kind: str | None = None) -> list[dict]`

- [ ] **Step 1: Add failing artifact store tests**

Create tests for note links, Wiki page persistence, and output persistence after reopening the SQLite store.

- [ ] **Step 2: Add SQLite tables**

Add:

```sql
CREATE TABLE IF NOT EXISTS note_links (
  note_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  PRIMARY KEY (note_id, source_type, source_id)
);

CREATE TABLE IF NOT EXISTS wiki_pages (
  page_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source_doc_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outputs (
  output_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source_doc_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

- [ ] **Step 3: Implement store methods**

Use JSON strings for source document IDs and return Python lists in response dictionaries.

- [ ] **Step 4: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_artifact_store -v
```

```powershell
git add backend/services/document_metadata_store.py backend/tests/test_artifact_store.py
git commit -m "feat: add artifact persistence schema"
```

## Task 2: Notes Link Upgrade

**Files:**

- Modify: `backend/services/note_service.py`
- Modify: `backend/api/notes.py`
- Modify: `backend/models/note.py`
- Modify: `frontend/src/views/NotesView.tsx`
- Modify: `frontend/src/components/ChatInterface.tsx`

**Interfaces:**

- Produces: `POST /api/notes/from-message`
- Produces note field: `links: Array<{ source_type: string; source_id: string }>`

- [ ] **Step 1: Add note link model fields**

Add `links` to note response models with default empty list.

- [ ] **Step 2: Add backend endpoint**

Endpoint body:

```json
{
  "message_index": 3,
  "conversation_id": "uuid",
  "title": "Claim about retrieval",
  "content": "Saved answer content",
  "doc_ids": ["doc-1"]
}
```

The endpoint creates a note and links it to the conversation/message and selected documents.

- [ ] **Step 3: Update Save as Note**

In `ChatInterface.tsx`, call `noteApi.createFromMessage()` instead of manually creating a generic note.

- [ ] **Step 4: Show links in NotesView**

Render linked source count and conversation link metadata in the note header.

- [ ] **Step 5: Verify and commit**

```powershell
cd frontend
npm run build
```

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m py_compile api/notes.py services/note_service.py models/note.py
```

```powershell
git add backend/services/note_service.py backend/api/notes.py backend/models/note.py frontend/src/views/NotesView.tsx frontend/src/components/ChatInterface.tsx frontend/src/services/api.ts
git commit -m "feat: link notes to sources and messages"
```

## Task 3: Outputs Service And API

**Files:**

- Create: `backend/services/output_service.py`
- Create: `backend/api/outputs.py`
- Modify: `backend/main.py`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/views/OutputsView.tsx`

**Interfaces:**

- Produces: `GET /api/outputs`
- Produces: `POST /api/outputs/generate`
- Produces: `GET /api/outputs/{output_id}`
- Produces: `DELETE /api/outputs/{output_id}`
- Produces: `POST /api/outputs/{output_id}/export`

- [ ] **Step 1: Create OutputService**

Supported `kind` values:

1. `summary`
2. `outline`
3. `review_cards`
4. `quiz`
5. `paper_plan`

Service builds prompts from selected doc IDs and calls `LLMService.generate()`.

- [ ] **Step 2: Create API router**

Return generated output shape:

```json
{
  "output_id": "uuid",
  "kind": "summary",
  "title": "Summary",
  "content": "markdown content",
  "source_doc_ids": ["doc-1"],
  "created_at": "2026-07-09T00:00:00",
  "updated_at": "2026-07-09T00:00:00"
}
```

- [ ] **Step 3: Register router**

Add `outputs` router to `backend/main.py`.

- [ ] **Step 4: Add frontend API and UI**

`OutputsView` should show:

1. Output kind selector.
2. Selected source count.
3. Generate button.
4. Persisted output list.
5. Markdown preview.

- [ ] **Step 5: Verify and commit**

```powershell
cd frontend
npm run build
```

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m py_compile api/outputs.py services/output_service.py main.py
```

```powershell
git add backend/services/output_service.py backend/api/outputs.py backend/main.py frontend/src/services/api.ts frontend/src/views/OutputsView.tsx
git commit -m "feat: add generated outputs"
```

## Task 4: Wiki Service And UI

**Files:**

- Create: `backend/services/wiki_service.py`
- Create: `backend/api/wiki.py`
- Modify: `backend/main.py`
- Modify: `frontend/src/components/ModuleNav.tsx`
- Modify: `frontend/src/store/useStore.ts`
- Create: `frontend/src/views/WikiView.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/services/api.ts`

**Interfaces:**

- Produces: `GET /api/wiki/pages`
- Produces: `POST /api/wiki/pages`
- Produces: `GET /api/wiki/pages/{page_id}`
- Produces: `PUT /api/wiki/pages/{page_id}`
- Produces: `POST /api/wiki/generate`

- [ ] **Step 1: Add `wiki` app module**

Extend `AppModule` with `wiki`. Add Wiki to `ModuleNav` and `App.tsx`.

- [ ] **Step 2: Create WikiService**

Support manual page creation, update, list, get, and source-grounded generation from selected documents.

- [ ] **Step 3: Create API router**

Use markdown content and return persisted page records.

- [ ] **Step 4: Create WikiView**

UI includes:

1. Page list.
2. Markdown preview.
3. Edit form.
4. Generate from selected sources action.
5. Source document IDs shown as provenance.

- [ ] **Step 5: Verify and commit**

```powershell
cd frontend
npm run build
```

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m py_compile api/wiki.py services/wiki_service.py main.py
```

```powershell
git add backend/services/wiki_service.py backend/api/wiki.py backend/main.py frontend/src/components/ModuleNav.tsx frontend/src/store/useStore.ts frontend/src/views/WikiView.tsx frontend/src/App.tsx frontend/src/services/api.ts
git commit -m "feat: add wiki pages"
```

## Task 5: Export Paths

**Files:**

- Modify: `backend/services/output_service.py`
- Modify: `backend/api/outputs.py`
- Modify: `frontend/src/views/OutputsView.tsx`
- Modify: `frontend/src/components/ExportModal.tsx`

**Interfaces:**

- Produces markdown export for outputs.
- Produces markdown export for Wiki pages.

- [ ] **Step 1: Add markdown export**

Return:

```json
{
  "filename": "summary.md",
  "content_type": "text/markdown",
  "content": "# Summary\n..."
}
```

- [ ] **Step 2: Add frontend download**

Use `Blob` and `URL.createObjectURL()` to download markdown content.

- [ ] **Step 3: Verify and commit**

```powershell
cd frontend
npm run build
```

```powershell
git add backend/services/output_service.py backend/api/outputs.py frontend/src/views/OutputsView.tsx frontend/src/components/ExportModal.tsx
git commit -m "feat: export generated artifacts"
```

## Task 6: Phase Verification

- [ ] **Step 1: Run global verification commands from the roadmap index**

- [ ] **Step 2: Manual acceptance**

Confirm:

1. Save an answer as a linked note.
2. Generate a summary from selected sources.
3. Generate a paper plan from selected sources.
4. Create and edit a Wiki page.
5. Export an output as Markdown.
6. Restart backend and confirm notes, Wiki pages, and outputs remain.

- [ ] **Step 3: Push**

```powershell
git status -sb
git push
```

## Done Criteria

Phase 4 is complete when:

1. Notes link to source documents and chat messages.
2. Outputs are generated, listed, previewed, persisted, and exportable.
3. Wiki pages are generated, editable, persisted, and source-grounded.
4. Global verification commands pass.

