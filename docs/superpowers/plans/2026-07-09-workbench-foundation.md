# Workbench Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first stable workbench foundation: fixed frontend build, centralized API calls, safe settings status, read-only Settings UI, document metadata persistence, and status polling.

**Architecture:** Keep FastAPI routes thin and place business logic in services. Keep secrets in backend `.env` only; frontend receives safe status only. Use a shared frontend API client so components do not hardcode backend URLs.

**Tech Stack:** FastAPI, Pydantic, SQLite from Python stdlib, React 18, TypeScript, Vite, TailwindCSS, Zustand, lucide-react.

## Global Constraints

- API keys must stay only in backend `.env`.
- Frontend must not render, receive, store, or submit raw API keys.
- Provider switching is done by editing `.env` and restarting backend.
- OpenAI is the primary provider; DashScope and OpenAI-compatible providers remain supported.
- ChromaDB remains the vector store.
- First-phase persistence uses SQLite for document metadata.
- The UI should feel like a compact workbench, not a landing page.
- Commit after each independently working task.

---

## File Structure

- `backend/core/config.py`: environment-backed settings.
- `backend/api/settings.py`: new safe settings status and LLM test routes.
- `backend/services/llm_service.py`: provider validation and lightweight test generation support.
- `backend/services/document_metadata_store.py`: new SQLite persistence for document metadata.
- `backend/services/document_service.py`: use SQLite metadata instead of volatile in-memory metadata only.
- `backend/api/documents.py`: keep route contract stable while relying on the updated service.
- `frontend/src/services/api.ts`: single frontend API surface for documents, chat, notes, settings, and streaming URL helpers.
- `frontend/src/components/UploadModal.tsx`: use shared document API, support DOCX and URL import, remove hardcoded backend URL.
- `frontend/src/components/ChatInterface.tsx`: remove hardcoded backend URL, fix nullable conversation ID type, keep streaming behavior.
- `frontend/src/components/NotesModal.tsx`: remove unused import and route requests through shared API.
- `frontend/src/components/SearchModal.tsx`: route note list through shared API.
- `frontend/src/components/ExportModal.tsx`: route note list through shared API.
- `frontend/src/components/SettingsModal.tsx`: new read-only settings panel.
- `frontend/src/App.tsx`: add Settings button and modal.
- `frontend/src/store/useStore.ts`: keep app state; add no secrets.

---

### Task 1: Build Fixes And Centralized API Surface

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/components/ChatInterface.tsx`
- Modify: `frontend/src/components/UploadModal.tsx`
- Modify: `frontend/src/components/NotesModal.tsx`
- Modify: `frontend/src/components/SearchModal.tsx`
- Modify: `frontend/src/components/ExportModal.tsx`

**Interfaces:**
- Produces: `API_BASE_URL = "/api"`
- Produces: `chatApi.createStreamRequest(data: ChatAskRequest): Promise<Response>`
- Produces: `documentApi.upload(file: File): Promise<UploadResponse>`
- Produces: `documentApi.uploadUrl(url: string): Promise<UploadResponse>`
- Produces: `noteApi.list(): Promise<NoteListResponse>`
- Produces: `noteApi.create(data: NoteCreateRequest): Promise<{ note_id: string; message: string }>`
- Produces: `noteApi.update(noteId: string, data: NoteUpdateRequest): Promise<{ message: string }>`
- Produces: `noteApi.delete(noteId: string): Promise<{ message: string }>`

- [ ] **Step 1: Run current frontend build and capture baseline failure**

Run: `npm run build` from `frontend`

Expected: FAIL with existing TypeScript errors in `ChatInterface.tsx` and `NotesModal.tsx`.

- [ ] **Step 2: Extend `frontend/src/services/api.ts`**

Add typed request/response interfaces, note APIs, URL upload API, and a stream helper that returns raw `fetch` Response for SSE:

```typescript
export const API_BASE_URL = '/api'

export interface ChatAskRequest {
  question: string
  doc_ids?: string[]
  conversation_id?: string | null
  history?: Array<{ role: string; content: string }>
}

export const chatApi = {
  ask: async (data: ChatAskRequest) => {
    const response = await api.post('/chat/ask', data)
    return response.data
  },
  createStreamRequest: async (data: ChatAskRequest) => {
    return fetch(`${API_BASE_URL}/chat/ask-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
  },
  suggestQuestions: async (docIds: string[]) => {
    const response = await api.post('/chat/suggest-questions', docIds)
    return response.data
  },
}
```

- [ ] **Step 3: Update `ChatInterface.tsx`**

Import `chatApi`, remove `API_BASE_URL`, replace direct fetch calls with `chatApi.suggestQuestions()` and `chatApi.createStreamRequest()`. Fix `streamConversationId` as `string | null` and call `setConversationId` only when the value is truthy:

```typescript
let streamConversationId: string | null = conversationId

if (data.type === 'start') {
  streamConversationId = data.conversation_id
  if (!conversationId && streamConversationId) {
    setConversationId(streamConversationId)
  }
}
```

- [ ] **Step 4: Update upload path and file types**

In `UploadModal.tsx`, replace direct fetch to `/upload` with `documentApi.upload(selectedFile)`. Accept `.pdf,.txt,.md,.docx` and allow DOCX MIME types. Keep API key unrelated to this component.

- [ ] **Step 5: Update notes/search/export API calls**

Replace direct `fetch("http://localhost:8000/api/notes/...")` calls with `noteApi` methods in `NotesModal.tsx`, `SearchModal.tsx`, and `ExportModal.tsx`. Remove unused `useCallback` from `NotesModal.tsx`.

- [ ] **Step 6: Run frontend build**

Run: `npm run build` from `frontend`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/services/api.ts frontend/src/components/ChatInterface.tsx frontend/src/components/UploadModal.tsx frontend/src/components/NotesModal.tsx frontend/src/components/SearchModal.tsx frontend/src/components/ExportModal.tsx
git commit -m "fix: stabilize frontend api wiring"
```

---

### Task 2: Safe Backend Settings Endpoints

**Files:**
- Create: `backend/api/settings.py`
- Modify: `backend/main.py`
- Modify: `backend/services/llm_service.py`

**Interfaces:**
- Produces: `GET /api/settings/status`
- Produces: `POST /api/settings/test-llm`
- Produces safe response fields: `provider`, `model`, `base_url_configured`, `api_key_configured`, `temperature`, `max_tokens`, `top_k`, `embedding_model`, `embedding_device`, `warnings`

- [ ] **Step 1: Create `backend/api/settings.py`**

Implement a router that returns safe configuration values and never returns `LLM_API_KEY`.

- [ ] **Step 2: Add LLM test endpoint**

The endpoint should call the configured provider with a tiny prompt and return:

```json
{
  "ok": true,
  "message": "LLM connection succeeded"
}
```

On failure it should return `ok: false` and a sanitized error message.

- [ ] **Step 3: Register router in `backend/main.py`**

Add:

```python
from api import documents, chat, notes, settings as settings_api
app.include_router(settings_api.router, prefix="/api/settings", tags=["Settings"])
```

- [ ] **Step 4: Run backend compile check**

Run:

```bash
python -m py_compile backend/main.py backend/api/settings.py backend/services/llm_service.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api/settings.py backend/main.py backend/services/llm_service.py
git commit -m "feat: add safe settings status api"
```

---

### Task 3: Read-Only Settings UI

**Files:**
- Create: `frontend/src/components/SettingsModal.tsx`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `settingsApi.getStatus(): Promise<SettingsStatus>`
- Consumes: `settingsApi.testLlm(): Promise<SettingsTestResult>`
- Produces: a settings modal opened from the top toolbar.

- [ ] **Step 1: Add `settingsApi` to `frontend/src/services/api.ts`**

Add typed `getStatus()` and `testLlm()` methods.

- [ ] **Step 2: Create `SettingsModal.tsx`**

Build a read-only panel with provider, model, API key configured/missing, base URL state, temperature, max tokens, top K, embedding model/device, warnings, and a test button. Do not include any API key input.

- [ ] **Step 3: Wire Settings button in `App.tsx`**

Use the lucide `Settings` icon and open the modal from the toolbar.

- [ ] **Step 4: Run frontend build**

Run: `npm run build` from `frontend`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/api.ts frontend/src/components/SettingsModal.tsx frontend/src/App.tsx
git commit -m "feat: add read-only settings panel"
```

---

### Task 4: SQLite Document Metadata Persistence And Status Polling

**Files:**
- Create: `backend/services/document_metadata_store.py`
- Modify: `backend/services/document_service.py`
- Modify: `frontend/src/components/UploadModal.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/services/api.ts`

**Interfaces:**
- Produces: `DocumentMetadataStore.upsert_document(metadata, source_path=None, source_url=None, source_type="file")`
- Produces: `DocumentMetadataStore.get_document(doc_id: str) -> Optional[dict]`
- Produces: `DocumentMetadataStore.list_documents() -> list[dict]`
- Produces: `DocumentMetadataStore.update_status(doc_id, status, total_chunks=0, summary=None, error_message=None)`
- Produces: document list survives backend restart.

- [ ] **Step 1: Add SQLite metadata store**

Create `backend/services/document_metadata_store.py` using stdlib `sqlite3`, storing the table from the design spec at `backend/data/notebooklm.db` by default.

- [ ] **Step 2: Refactor `DocumentService`**

Replace document metadata reads and writes with the SQLite store. Keep in-memory values only for transient processing context when necessary.

- [ ] **Step 3: Add frontend polling**

After upload, poll `/api/documents/{doc_id}/status` until `completed` or `failed`, then refresh document list.

- [ ] **Step 4: Run backend compile check**

Run:

```bash
python -m py_compile backend/services/document_metadata_store.py backend/services/document_service.py backend/api/documents.py
```

Expected: PASS.

- [ ] **Step 5: Run frontend build**

Run: `npm run build` from `frontend`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/services/document_metadata_store.py backend/services/document_service.py frontend/src/components/UploadModal.tsx frontend/src/components/Sidebar.tsx frontend/src/services/api.ts
git commit -m "feat: persist document metadata"
```

---

### Task 5: Verification And Push

**Files:**
- Modify as needed only for small fixes discovered during verification.

**Interfaces:**
- Produces: branch `phase1-workbench-foundation` pushed to origin.

- [ ] **Step 1: Run backend compile check**

Run:

```bash
python -m py_compile backend/main.py backend/api/*.py backend/services/*.py backend/models/*.py backend/core/*.py
```

Expected: PASS.

- [ ] **Step 2: Run frontend build**

Run: `npm run build` from `frontend`

Expected: PASS.

- [ ] **Step 3: Inspect git status**

Run: `git status -sb`

Expected: clean working tree.

- [ ] **Step 4: Push branch**

Run:

```bash
git push -u origin phase1-workbench-foundation
```

Expected: branch pushed to GitHub.

---

## Self-Review

Spec coverage:

- Stable build is covered by Task 1 and Task 5.
- Safe `.env`-only settings are covered by Task 2 and Task 3.
- Workbench UI begins with Settings wiring in Task 3 and avoids broad redesign until the foundation is stable.
- Document metadata persistence is covered by Task 4.
- Existing streaming chat remains covered by Task 1.

Placeholder scan:

- No `TBD`, `TODO`, or undefined follow-up placeholders are intentionally left in the plan.

Type consistency:

- `ChatAskRequest`, `settingsApi`, `noteApi`, and `DocumentMetadataStore` names are defined before use.

