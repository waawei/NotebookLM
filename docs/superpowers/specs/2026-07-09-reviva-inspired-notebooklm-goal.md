# Reviva-Inspired NotebookLM Goal

Date: 2026-07-09

## Decision

The project will pivot toward a Reviva-inspired local knowledge workbench, but it will not copy Reviva source code or switch to Reviva's Electron/Vue architecture in the first migration.

The product direction is:

1. Learn Reviva's UI structure and module layout.
2. Keep the current React frontend and FastAPI backend.
3. Keep RAG, model calls, document parsing, and answer-quality work in Python.
4. Continue evolving SQLite metadata plus ChromaDB vector storage.
5. Reimplement Agents and Skills later using our own service boundaries.
6. Keep API keys only in backend `.env`; the UI shows configured/missing status only.

## Why This Direction

Reviva is close to the desired product shape: local-first materials, learning workspace, Wiki knowledge base, chat, notes, creation tools, Agents, Skills, and multi-provider model configuration.

However, direct adoption has three costs:

1. Tech-stack reset: Reviva uses Electron, Vue, Pinia, SQLite, LangChain, and DeepAgents. This would discard much of the current FastAPI/React/RAG work.
2. License risk: Reviva is AGPL-3.0 plus commercial licensing. Copying substantial source code would impose license obligations on our project.
3. Complexity jump: Electron IPC, native SQLite bindings, local desktop packaging, and Agent orchestration are all useful but add operational complexity before our core Q&A loop is mature.

The safer path is to adopt the product architecture and interaction model while reimplementing features inside the current stack.

## Product Goal

Build a stable, local-first NotebookLM-style knowledge workbench for:

1. Students reviewing course materials.
2. Paper writers reading, comparing, outlining, and citing sources.
3. Small teams using a local company knowledge base.

The product should feel like a serious workbench, not a chat demo:

1. Sources are always visible and manageable.
2. Chat answers are grounded in selected materials.
3. Citations and retrieval evidence are inspectable.
4. Notes, summaries, outlines, and generated outputs become reusable artifacts.
5. Model configuration is clear, safe, and provider-agnostic.

## Non-Goals

1. Do not copy Reviva source code into this repository.
2. Do not switch to Electron/Vue in the first migration.
3. Do not store API keys in frontend state, browser storage, or UI-managed settings.
4. Do not build a full Agent/Skills system before the core workbench, retrieval, and answer quality are stable.
5. Do not introduce user accounts, cloud sync, or multi-tenant permissions yet.

## Architecture Strategy

### Frontend

Keep React, TypeScript, Vite, TailwindCSS, Zustand, and lucide-react.

The frontend should move toward a Reviva-like module shell:

1. `Dashboard`: overview of recent sources, conversations, notes, outputs, and model status.
2. `Workbench`: main learning/chat surface with source selection, modes, streaming answers, citations, and note capture.
3. `Sources`: document and URL library with processing state, tags, spaces, and search.
4. `Notes`: persistent user notes linked to sources, chats, and outputs.
5. `Wiki`: curated knowledge pages generated from selected sources, implemented after source/chat stability.
6. `Outputs`: generated artifacts such as summaries, outlines, review cards, quizzes, paper plans, and reports.
7. `Settings`: read-only runtime status from `.env`.
8. `Agents` and `Skills`: later modules, initially hidden or marked as roadmap-only.

### Backend

Keep FastAPI as the service boundary.

Target backend modules:

1. `api/`: thin route definitions.
2. `services/document_service.py`: file ingestion, parsing, chunking, metadata updates.
3. `services/rag_service.py`: retrieval, reranking, context building, citation preparation.
4. `services/llm_service.py`: OpenAI, DashScope, OpenAI-compatible, and local model calls.
5. `services/settings_service.py`: safe config status, provider validation, connection tests.
6. `services/note_service.py`: notes CRUD and source/chat linking.
7. `services/output_service.py`: generated artifacts and exportable content.
8. `services/wiki_service.py`: curated pages built from source sets.
9. `services/job_service.py`: background processing states for ingestion and generation.
10. `services/agent_service.py`: later orchestration layer for Agents/Skills.

### Data Layer

Use SQLite for durable app metadata and ChromaDB for vector retrieval.

SQLite owns:

1. Documents and source metadata.
2. Spaces or collections.
3. Conversations and messages.
4. Notes.
5. Wiki pages.
6. Outputs.
7. Jobs and processing errors.
8. Model invocation logs without secrets.

ChromaDB owns:

1. Chunk embeddings.
2. Chunk text.
3. Chunk-to-document metadata.
4. Retrieval metadata such as page, section, and source path when available.

Local files remain on disk. SQLite stores normalized references to them.

## API Surface

The frontend should call only `/api/...` through `frontend/src/services/api.ts`.

### Settings

1. `GET /api/settings/status`
2. `POST /api/settings/test-llm`

Rules:

1. Never return raw API keys.
2. Show only configured/missing.
3. Show provider, model, base URL configured/default, temperature, max tokens, top K, embedding model, and device.

### Sources

1. `GET /api/documents`
2. `POST /api/documents/upload`
3. `POST /api/documents/upload-url`
4. `GET /api/documents/{doc_id}/status`
5. `DELETE /api/documents/{doc_id}`
6. `POST /api/documents/search`

### Workbench Chat

1. `POST /api/chat/ask-stream`
2. `POST /api/chat/ask`
3. `GET /api/chat/conversations`
4. `GET /api/chat/conversations/{conversation_id}`
5. `DELETE /api/chat/conversations/{conversation_id}`
6. `POST /api/chat/suggest-questions`

### Notes

1. `GET /api/notes`
2. `POST /api/notes`
3. `PUT /api/notes/{note_id}`
4. `DELETE /api/notes/{note_id}`
5. `POST /api/notes/from-message`

### Outputs

1. `GET /api/outputs`
2. `POST /api/outputs/generate`
3. `GET /api/outputs/{output_id}`
4. `DELETE /api/outputs/{output_id}`
5. `POST /api/outputs/{output_id}/export`

### Wiki

1. `GET /api/wiki/pages`
2. `POST /api/wiki/pages`
3. `GET /api/wiki/pages/{page_id}`
4. `PUT /api/wiki/pages/{page_id}`
5. `POST /api/wiki/generate`

Agents and Skills APIs are intentionally deferred.

## Workbench UI Details

### App Shell

Use a dense workbench layout:

1. Left rail: module navigation.
2. Left panel: source or module list.
3. Center panel: active workspace.
4. Right inspector: citations, retrieval hits, notes, settings status, or generation details.
5. Top toolbar: global search, active model status, settings, theme, and run state.

Do not build a marketing landing page.

### Workbench Modes

The first set of modes should be prompt presets:

1. `Review`: explains concepts, generates study questions, and highlights gaps.
2. `Paper`: extracts claims, evidence, citations, counterpoints, and outline suggestions.
3. `Knowledge Base`: answers directly with strict source grounding.

Mode should affect prompts and citation strictness, not split the whole backend.

### Citation Inspector

Every answer should expose:

1. Source filename or URL.
2. Page or section if available.
3. Retrieved text snippet.
4. Relevance score if available.
5. Click action to open source preview or focus the source item.

### Settings UI

Settings remains read-only:

1. Provider.
2. Model.
3. API key configured or missing.
4. Base URL default or custom configured.
5. Temperature.
6. Max tokens.
7. Top K.
8. Embedding model.
9. Embedding device.
10. Test LLM result.

The UI must not contain an API key input.

## Answer Quality Plan

Answer quality depends on the model, but the application controls retrieval quality and context quality.

Priority improvements:

1. Preserve document structure during parsing: title, headings, page numbers, sections, tables when possible.
2. Chunk by semantic boundaries instead of fixed text length only.
3. Add query rewriting for vague questions.
4. Add hybrid retrieval later: vector retrieval plus keyword retrieval.
5. Add reranking for top chunks.
6. Build compact source context with clear citation IDs.
7. Add mode-specific system prompts.
8. Add a small evaluation set of 3-5 real documents and expected questions.

## Provider Configuration

Secrets live only in backend `.env`.

Primary OpenAI example:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...
LLM_BASE_URL=
```

OpenAI-compatible remote endpoint:

```env
LLM_PROVIDER=openai_compatible
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=...
LLM_BASE_URL=https://example.com/v1
```

Local Ollama-style Qwen 8B:

```env
LLM_PROVIDER=openai_compatible
LLM_MODEL=qwen2.5:8b
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
```

Local LM Studio-style Qwen 8B:

```env
LLM_PROVIDER=openai_compatible
LLM_MODEL=qwen2.5-8b-instruct
LLM_API_KEY=lm-studio
LLM_BASE_URL=http://localhost:1234/v1
```

The backend should normalize compatible base URLs where safe, but the status endpoint should warn when a URL looks invalid.

## Implementation Phases

### Phase 1: Reviva-Like Shell On Current Stack

Goal: make the product feel like a workbench without changing core backend architecture.

Tasks:

1. Add module navigation shell.
2. Split the UI into Dashboard, Workbench, Sources, Notes, Outputs, Settings.
3. Keep current chat and upload flows working.
4. Add right inspector for citations and settings status.
5. Keep all API calls routed through `frontend/src/services/api.ts`.

Acceptance criteria:

1. Frontend builds.
2. Backend starts.
3. Upload, document list, chat, citations, notes, and settings still work.
4. UI no longer feels like a single-purpose chat page.

### Phase 2: Sources, Spaces, And Persistent Workflows

Goal: make source management reliable enough for real study and paper workflows.

Tasks:

1. Add spaces or collections in SQLite.
2. Add document tags and source grouping.
3. Add source search and filters.
4. Improve status polling and processing error display.
5. Persist conversations in SQLite if current storage is weaker than needed.

Acceptance criteria:

1. User can manage 3-5 real files as one workspace.
2. Document status survives restart.
3. User can select a subset of sources for chat.

### Phase 3: Answer Quality Upgrade

Goal: improve answer reliability before adding heavy Agent features.

Tasks:

1. Improve chunking with structure-aware metadata.
2. Add query rewriting.
3. Add reranking or hybrid retrieval.
4. Improve citation formatting and source grounding.
5. Add a small evaluation set.

Acceptance criteria:

1. Answers cite relevant sources consistently.
2. The same question over the same files is stable enough for demo use.
3. The app can handle student review, paper outline, and company KB questions with different prompt modes.

### Phase 4: Notes, Wiki, And Outputs

Goal: turn chat results into reusable knowledge artifacts.

Tasks:

1. Link notes to documents, chunks, and messages.
2. Add generated outputs: summary, outline, review cards, quiz, paper plan.
3. Add Wiki pages generated from selected sources.
4. Add export paths for Markdown and basic document formats.

Acceptance criteria:

1. User can create an answer, save useful parts as notes, and generate an artifact from selected notes/sources.
2. Wiki pages can be regenerated or manually edited.

### Phase 5: Agents And Skills

Goal: reimplement Reviva-like Agents and Skills after core workbench quality is proven.

Tasks:

1. Define a minimal skill manifest format.
2. Add backend tool registry.
3. Add safe tool execution boundaries.
4. Add agent runs with visible steps and outputs.
5. Add skills for paper planning, course review, report generation, and knowledge-base maintenance.

Acceptance criteria:

1. Agent runs are inspectable.
2. Skills operate on local sources without exposing secrets.
3. Failed tool calls are recoverable and visible to users.

## Engineering Rules

1. Commit after each independently working phase or narrow feature.
2. Keep changes scoped; do not rewrite the stack unless a phase explicitly requires it.
3. Run frontend build and backend checks before claiming a phase is complete.
4. Keep secrets out of frontend code and git.
5. Prefer explicit service boundaries over hidden global state.
6. Keep UI dense, calm, and task-oriented.
7. Use Reviva as a product reference, not as a code source.

## Near-Term Next Step

Create an implementation plan for Phase 1:

1. Audit current UI components and state.
2. Design the new shell layout.
3. Move existing components into module views without breaking behavior.
4. Add Dashboard and Workbench entry points.
5. Add right inspector structure.
6. Build and verify.

