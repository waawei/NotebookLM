# NotebookLM Workbench Settings Design

Date: 2026-07-09

## Context

The project is a local NotebookLM-style RAG application for students, paper writing, and company knowledge-base use cases. The current architecture is already split into a FastAPI backend and a React/Vite frontend. The backend has useful capabilities such as streaming chat, document parsing, ChromaDB search, notes, URL upload, and conversation persistence. The frontend exposes a workspace-like shell but has unstable API wiring and currently fails TypeScript build.

The next optimization should make the app reliable first, then turn it into a polished knowledge workbench.

## Goals

1. Make the current project stable to build and run.
2. Convert the UI direction into a workbench-style knowledge base.
3. Add a safe read-only Settings panel for provider/model/runtime status.
4. Keep API keys only in the backend `.env`.
5. Support OpenAI as the primary provider and keep multi-provider switching through `.env`.
6. Persist document metadata so documents do not disappear from the UI after backend restart.
7. Expose existing backend features through a coherent frontend flow.

## Non-Goals

1. The first phase will not let the UI edit or save API keys.
2. The first phase will not build user accounts or cloud sync.
3. The first phase will not replace ChromaDB.
4. The first phase will not introduce complex RAG evaluation tooling.
5. Provider switching will be done by editing `.env` and restarting the backend, not live switching in the UI.

## Target Users

The app should support three overlapping user groups:

1. Students reviewing course material.
2. Paper writers reading, comparing, summarizing, and citing sources.
3. Teams using a local company knowledge base for document Q&A.

The interface should feel like a dense knowledge workbench, not a marketing page or simple chat demo.

## Product Shape

The first viewport should be the actual workbench:

1. Left sidebar: Sources.
2. Center panel: Chat and workspace.
3. Right inspector: citations, note context, retrieval hits, and settings status.
4. Top toolbar: search, export, settings, theme, and global status.

The UI should prioritize scanability, clear states, and repeated work. Cards should be used for repeated source/message/citation items, while the page itself should use full-height panels instead of stacked decorative cards.

## Architecture

### Backend

The backend remains FastAPI with these boundaries:

1. `api/`: route definitions only.
2. `services/`: business logic, RAG orchestration, persistence, provider calls.
3. `models/`: Pydantic request/response models.
4. `core/config.py`: environment-backed settings.

Add a small configuration status surface:

`GET /api/settings/status`

Returns only safe, non-secret values:

```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "base_url_configured": false,
  "api_key_configured": true,
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_k": 5,
  "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
  "embedding_device": "cpu"
}
```

Add an optional model connectivity check:

`POST /api/settings/test-llm`

The endpoint uses the backend `.env` credentials and returns success/failure without exposing secrets.

### Frontend

Frontend API calls should go through `frontend/src/services/api.ts`.

Remove component-level hardcoded backend URLs such as `http://localhost:8000`. The Vite proxy already supports `/api`, and a single API client is enough for local development.

Add a Settings panel/modal or right-inspector tab that displays:

1. Backend status.
2. Provider.
3. Model.
4. API key configured or missing.
5. Base URL default or custom configured.
6. Temperature.
7. Max tokens.
8. Top K.
9. Embedding model/device.
10. LLM connection test result.

The UI must not render, receive, store, or submit raw API keys.

## Configuration Policy

`.env` is the only source for secrets.

Example:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...
LLM_BASE_URL=
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
TOP_K_RESULTS=5
```

Supported providers:

1. `openai`
2. `dashscope`
3. `openai_compatible`

For `openai_compatible`, `LLM_BASE_URL` must be configured. The backend should validate this at startup or in the status endpoint and return clear configuration warnings.

## Data Flow

### Upload Flow

1. User uploads a file or adds a URL from the Sources panel.
2. Frontend sends request through the shared API client.
3. Backend stores the source and creates metadata.
4. Backend processes the source in the background.
5. Frontend polls document status until completed or failed.
6. Completed documents become selectable for chat.

The first phase must fix the upload endpoint mismatch:

Frontend should call `/api/documents/upload`, not `/upload`.

### Chat Flow

1. User selects one or more sources.
2. User asks a question in the center workspace.
3. Frontend calls `/api/chat/ask-stream`.
4. Backend retrieves relevant chunks from ChromaDB.
5. Backend streams answer chunks through SSE.
6. Backend sends citations after generation.
7. Frontend updates the answer progressively and shows citations in the inspector or under the answer.

### Settings Flow

1. User opens Settings.
2. Frontend calls `/api/settings/status`.
3. Frontend displays safe config state.
4. User can run a test connection.
5. If config is invalid, UI explains that `.env` must be edited and backend restarted.

## Persistence

The current `documents_meta` in-memory dictionary is not sufficient because document metadata is lost after backend restart. First-phase persistence should use SQLite for document metadata.

Minimum table:

```sql
CREATE TABLE documents (
  doc_id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  upload_time TEXT NOT NULL,
  status TEXT NOT NULL,
  total_chunks INTEGER NOT NULL DEFAULT 0,
  summary TEXT,
  error_message TEXT,
  source_type TEXT NOT NULL DEFAULT 'file',
  source_path TEXT,
  source_url TEXT
);
```

ChromaDB continues to hold vector data. SQLite holds user-facing metadata and processing state.

Notes and conversations may stay as JSON files in the first phase, but their API access should still go through the shared frontend API client.

## Error Handling

Backend errors should return actionable messages without leaking secrets.

Important cases:

1. Missing API key.
2. Unsupported provider.
3. Invalid base URL.
4. LLM connection failure.
5. Unsupported file type.
6. File too large.
7. Document processing failure.
8. Empty retrieval result.

Frontend should replace `alert()` with existing toast behavior where possible.

## UI Direction

The UI should become more compact and work-focused:

1. Left panel: source list, upload button, URL import, source states, selected count.
2. Center panel: chat stream, suggested questions, mode selector.
3. Right panel: citations, retrieval hits, notes, settings status.
4. Top toolbar: search, export, settings, theme.

Initial modes:

1. Review: concise explanations and study questions.
2. Paper: structured summaries, claims, evidence, citation-focused output.
3. Knowledge Base: direct factual answers with source grounding.

Modes can be implemented as prompt presets after the stable foundation is complete.

## Testing

Minimum verification for phase one:

1. `python -m py_compile` for backend modules.
2. `npm run build` for frontend.
3. Upload a TXT or PDF source through the UI.
4. Confirm document status moves from processing to completed.
5. Ask a streaming question and receive citations.
6. Restart backend and confirm document list still appears.
7. Open Settings and confirm API key is shown only as configured/missing.
8. Run LLM test endpoint with configured and missing key scenarios.

## Implementation Phases

### Phase 1: Stable Workbench Foundation

1. Fix TypeScript build errors.
2. Fix upload endpoint path.
3. Route frontend API calls through `services/api.ts`.
4. Add safe settings status endpoint.
5. Add Settings UI.
6. Add SQLite document metadata persistence.
7. Add status polling and better toasts.

### Phase 2: Feature Completion

1. Add URL import to the upload flow.
2. Ensure DOCX support is visible in UI.
3. Improve notes workflow.
4. Improve export workflow.
5. Add right-side citation/retrieval inspector.
6. Add work modes for review, paper, and knowledge base.

### Phase 3: Answer Quality

1. Add query rewriting.
2. Add reranking or hybrid retrieval.
3. Improve citation placement.
4. Preserve page/source metadata more accurately.
5. Add small evaluation document set and expected questions.

## Acceptance Criteria

Phase one is complete when:

1. Frontend builds successfully.
2. Backend starts successfully.
3. Upload works through the UI.
4. Chat streams answers with citations.
5. Settings shows provider/model/config status without exposing API keys.
6. Document metadata survives backend restart.
7. All component-level hardcoded backend URLs are removed.

