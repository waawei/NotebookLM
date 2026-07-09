# Reviva-Inspired Phase 2 Sources Spaces Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make source management reliable enough for real study, paper-writing, and local knowledge-base workflows.

**Architecture:** Extend the existing SQLite metadata layer instead of introducing a new database. Keep ChromaDB as the vector store and add workspace metadata around documents, spaces, tags, jobs, and conversations.

**Tech Stack:** FastAPI, Python stdlib `sqlite3`, Pydantic, React 18, TypeScript, Vite, Zustand, ChromaDB.

## Global Constraints

- Do not copy Reviva source code.
- Do not switch to Electron or Vue.
- Do not add API key inputs to the UI.
- Keep all frontend API calls in `frontend/src/services/api.ts`.
- Keep ChromaDB as the vector store.
- Keep secrets only in backend `.env`.
- Commit after each independently working task.

---

## File Structure

- Modify: `backend/services/document_metadata_store.py` for spaces, tags, jobs, and conversation tables.
- Create: `backend/tests/test_metadata_store.py` for SQLite persistence tests.
- Modify: `backend/models/document.py` for space, tag, and job response models.
- Modify: `backend/api/documents.py` for source search/filter endpoints.
- Create: `backend/api/spaces.py` for space CRUD endpoints.
- Modify: `backend/main.py` to register the spaces router.
- Modify: `backend/services/chat_service.py` to persist conversations through SQLite.
- Modify: `frontend/src/services/api.ts` for spaces, tags, document filters, and conversations.
- Modify: `frontend/src/store/useStore.ts` for active space and source filters.
- Modify: `frontend/src/views/SourcesView.tsx` for spaces, tags, search, filters, and status detail.
- Modify: `frontend/src/views/DashboardView.tsx` for space-aware counts.
- Modify: `frontend/src/components/Sidebar.tsx` to respect the active space.

## Task 1: SQLite Schema Expansion

**Files:**

- Modify: `backend/services/document_metadata_store.py`
- Create: `backend/tests/test_metadata_store.py`

**Interfaces:**

- Produces: `DocumentMetadataStore.create_space(name: str, description: str = "") -> dict`
- Produces: `DocumentMetadataStore.list_spaces() -> list[dict]`
- Produces: `DocumentMetadataStore.assign_document_to_space(doc_id: str, space_id: str) -> None`
- Produces: `DocumentMetadataStore.set_document_tags(doc_id: str, tags: list[str]) -> None`
- Produces: `DocumentMetadataStore.search_documents(query: str = "", space_id: str | None = None, tags: list[str] | None = None, status: str | None = None) -> list[dict]`

- [ ] **Step 1: Add failing SQLite persistence tests**

Create `backend/tests/test_metadata_store.py`:

```python
import os
import tempfile
import unittest

from services.document_metadata_store import DocumentMetadataStore


class MetadataStorePhase2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        self.store = DocumentMetadataStore(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_space_assignment_and_tag_filtering_survive_reopen(self):
        self.store.upsert_document({
            "doc_id": "doc-1",
            "filename": "paper.pdf",
            "file_type": "pdf",
            "file_size": 100,
            "upload_time": "2026-07-09T00:00:00",
            "status": "completed",
            "total_chunks": 3,
            "summary": "paper summary",
        })
        space = self.store.create_space("Thesis", "paper writing")
        self.store.assign_document_to_space("doc-1", space["space_id"])
        self.store.set_document_tags("doc-1", ["paper", "review"])

        reopened = DocumentMetadataStore(self.db_path)
        results = reopened.search_documents(space_id=space["space_id"], tags=["paper"], status="completed")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["doc_id"], "doc-1")
        self.assertEqual(results[0]["space_id"], space["space_id"])
        self.assertEqual(results[0]["tags"], ["paper", "review"])
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_metadata_store -v
```

Expected: FAIL because `create_space` is not defined.

- [ ] **Step 3: Add tables and methods**

Update `DocumentMetadataStore._init_db()` with:

```sql
CREATE TABLE IF NOT EXISTS spaces (
  space_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_spaces (
  doc_id TEXT NOT NULL,
  space_id TEXT NOT NULL,
  PRIMARY KEY (doc_id, space_id),
  FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
  FOREIGN KEY (space_id) REFERENCES spaces(space_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_tags (
  doc_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  PRIMARY KEY (doc_id, tag),
  FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);
```

Add Python methods with the exact signatures from the Interfaces section.

- [ ] **Step 4: Run metadata tests**

Run:

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_metadata_store -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/services/document_metadata_store.py backend/tests/test_metadata_store.py
git commit -m "feat: add source spaces and tags metadata"
```

## Task 2: Spaces API

**Files:**

- Create: `backend/api/spaces.py`
- Modify: `backend/main.py`
- Modify: `backend/models/document.py`

**Interfaces:**

- Produces: `GET /api/spaces`
- Produces: `POST /api/spaces`
- Produces: `PUT /api/spaces/{space_id}`
- Produces: `DELETE /api/spaces/{space_id}`
- Produces: `POST /api/spaces/{space_id}/documents/{doc_id}`

- [ ] **Step 1: Add Pydantic models**

Add to `backend/models/document.py`:

```python
class SpaceCreate(BaseModel):
    name: str
    description: str = ""


class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SpaceResponse(BaseModel):
    space_id: str
    name: str
    description: str
    created_at: str
    updated_at: str
```

- [ ] **Step 2: Create `backend/api/spaces.py`**

Implement router methods using `DocumentMetadataStore`. Return dictionaries shaped like:

```json
{
  "spaces": [
    {
      "space_id": "uuid",
      "name": "Thesis",
      "description": "paper writing",
      "created_at": "2026-07-09T00:00:00",
      "updated_at": "2026-07-09T00:00:00"
    }
  ]
}
```

- [ ] **Step 3: Register router**

Modify `backend/main.py`:

```python
from api import documents, chat, notes, settings as settings_api, spaces
app.include_router(spaces.router, prefix="/api/spaces", tags=["Spaces"])
```

- [ ] **Step 4: Compile backend**

Run:

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m py_compile api/spaces.py main.py models/document.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/api/spaces.py backend/main.py backend/models/document.py
git commit -m "feat: add spaces api"
```

## Task 3: Source Search And Filtering

**Files:**

- Modify: `backend/api/documents.py`
- Modify: `backend/models/document.py`
- Modify: `frontend/src/services/api.ts`

**Interfaces:**

- Produces: `POST /api/documents/search`
- Produces frontend: `documentApi.search(filters: DocumentSearchFilters)`

- [ ] **Step 1: Add request model**

Add to `backend/models/document.py`:

```python
class DocumentSearchRequest(BaseModel):
    query: str = ""
    space_id: Optional[str] = None
    tags: List[str] = []
    status: Optional[str] = None
```

- [ ] **Step 2: Add API endpoint**

Add to `backend/api/documents.py`:

```python
@router.post("/search")
async def search_documents(request: DocumentSearchRequest):
    results = document_service.metadata_store.search_documents(
        query=request.query,
        space_id=request.space_id,
        tags=request.tags,
        status=request.status,
    )
    return {"documents": results, "total": len(results)}
```

- [ ] **Step 3: Add frontend API types**

Add to `frontend/src/services/api.ts`:

```typescript
export interface DocumentSearchFilters {
  query?: string
  space_id?: string | null
  tags?: string[]
  status?: string | null
}

search: async (filters: DocumentSearchFilters): Promise<{ documents: DocumentItem[]; total: number }> => {
  const response = await api.post('/documents/search', filters)
  return response.data
}
```

- [ ] **Step 4: Verify**

Run:

```powershell
cd frontend
npm run build
```

Run:

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m py_compile api/documents.py models/document.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/api/documents.py backend/models/document.py frontend/src/services/api.ts
git commit -m "feat: add source search filters"
```

## Task 4: Sources UI With Spaces And Tags

**Files:**

- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/store/useStore.ts`
- Modify: `frontend/src/views/SourcesView.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/views/DashboardView.tsx`

**Interfaces:**

- Consumes: `documentApi.search(filters)`
- Consumes: `spacesApi.list()`, `spacesApi.create(data)`, `spacesApi.assignDocument(spaceId, docId)`
- Produces store fields: `activeSpaceId`, `sourceQuery`, `sourceStatusFilter`, `sourceTagFilter`

- [ ] **Step 1: Add frontend API**

Add to `frontend/src/services/api.ts`:

```typescript
export interface SpaceItem {
  space_id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export const spacesApi = {
  list: async (): Promise<{ spaces: SpaceItem[] }> => {
    const response = await api.get('/spaces')
    return response.data
  },
  create: async (data: { name: string; description?: string }): Promise<SpaceItem> => {
    const response = await api.post('/spaces', data)
    return response.data
  },
  assignDocument: async (spaceId: string, docId: string): Promise<{ message: string }> => {
    const response = await api.post(`/spaces/${spaceId}/documents/${docId}`)
    return response.data
  },
}
```

- [ ] **Step 2: Add store fields**

Add to `frontend/src/store/useStore.ts`:

```typescript
activeSpaceId: string | null
sourceQuery: string
sourceStatusFilter: string | null
sourceTagFilter: string[]
setActiveSpaceId: (spaceId: string | null) => void
setSourceQuery: (query: string) => void
setSourceStatusFilter: (status: string | null) => void
setSourceTagFilter: (tags: string[]) => void
```

- [ ] **Step 3: Update SourcesView**

Implement:

1. Space selector on top left.
2. Search input.
3. Status segmented control: All, Ready, Processing, Failed.
4. Tag display on source rows.
5. Assign selected source to active space.

- [ ] **Step 4: Update Sidebar and Dashboard**

Use `activeSpaceId` when loading documents. Show active space name and filtered counts.

- [ ] **Step 5: Verify**

Run:

```powershell
cd frontend
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add frontend/src/services/api.ts frontend/src/store/useStore.ts frontend/src/views/SourcesView.tsx frontend/src/components/Sidebar.tsx frontend/src/views/DashboardView.tsx
git commit -m "feat: add source spaces UI"
```

## Task 5: Conversation Persistence In SQLite

**Files:**

- Modify: `backend/services/document_metadata_store.py`
- Modify: `backend/services/chat_service.py`
- Create: `backend/tests/test_conversation_store.py`

**Interfaces:**

- Produces: `DocumentMetadataStore.save_conversation(conversation: dict) -> None`
- Produces: `DocumentMetadataStore.get_conversation(conversation_id: str) -> Optional[dict]`
- Produces: `DocumentMetadataStore.list_conversations() -> list[dict]`
- Produces: `DocumentMetadataStore.delete_conversation(conversation_id: str) -> bool`

- [ ] **Step 1: Add failing test**

Create `backend/tests/test_conversation_store.py` with a test that saves a conversation, reopens the store, lists it, gets it, deletes it, and confirms it is gone.

- [ ] **Step 2: Add SQLite tables**

Add:

```sql
CREATE TABLE IF NOT EXISTS conversations (
  conversation_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_messages (
  message_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  citations_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
);
```

- [ ] **Step 3: Refactor ChatService**

Replace JSON-file persistence with SQLite calls. Keep in-memory cache only as a read-through optimization.

- [ ] **Step 4: Verify**

Run:

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_conversation_store -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/services/document_metadata_store.py backend/services/chat_service.py backend/tests/test_conversation_store.py
git commit -m "feat: persist conversations in sqlite"
```

## Task 6: Phase Verification

**Files:**

- Modify only files needed for verification fixes.

- [ ] **Step 1: Run frontend build**

```powershell
cd frontend
npm run build
```

- [ ] **Step 2: Run backend tests**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

- [ ] **Step 3: Run backend compile check**

```powershell
cd backend
$env:DEBUG='false'
$files = Get-ChildItem -Recurse -Include *.py | Where-Object { $_.FullName -notmatch '\\venv\\' } | ForEach-Object { $_.FullName }
.\venv\Scripts\python.exe -m py_compile @files
```

- [ ] **Step 4: Manual acceptance**

Use 3-5 real files. Confirm:

1. Create a space.
2. Upload or select documents.
3. Assign documents to a space.
4. Filter by space/status/tag.
5. Ask a question with selected sources.
6. Restart backend.
7. Documents, spaces, tags, and conversation list remain visible.

- [ ] **Step 5: Commit final fixes and push**

```powershell
git status -sb
git push
```

## Done Criteria

Phase 2 is complete when:

1. Spaces and tags are persisted in SQLite.
2. Source search/filtering works from the Sources UI.
3. Conversations persist through backend restart.
4. The app can manage 3-5 real files in one named workspace.
5. Global verification commands pass.

