# Reviva-Inspired Phase 3 Answer Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve answer reliability, citation grounding, and mode-specific behavior before adding heavy Agent features.

**Architecture:** Keep the chat API stable while extracting retrieval and prompt assembly into focused services. Add a small evaluation harness so answer quality changes have measurable acceptance evidence.

**Tech Stack:** FastAPI, Python, unittest, sentence-transformers, ChromaDB, OpenAI-compatible chat APIs, React TypeScript.

## Global Constraints

- Do not copy Reviva source code.
- Do not switch to Electron or Vue.
- Do not expose API keys to the frontend.
- Keep `/api/chat/ask-stream` compatible with the current frontend stream parser.
- Keep all frontend API calls in `frontend/src/services/api.ts`.
- Commit after each independently working task.

---

## File Structure

- Create: `backend/services/retrieval_service.py` for query rewriting, retrieval, reranking, and context assembly.
- Modify: `backend/services/chat_service.py` to use `RetrievalService`.
- Modify: `backend/services/document_parser.py` for structure-aware chunks.
- Modify: `backend/services/vector_store.py` to store richer chunk metadata.
- Create: `backend/evals/quality_cases.json` for local evaluation cases.
- Create: `backend/tests/test_retrieval_service.py` for deterministic service tests.
- Create: `backend/tests/test_prompt_modes.py` for mode prompt tests.
- Modify: `backend/models/chat.py` to add `mode`.
- Modify: `frontend/src/components/ChatInterface.tsx` for mode selector.
- Modify: `frontend/src/components/RightInspector.tsx` for clearer retrieval evidence.

## Task 1: Retrieval Service Boundary

**Files:**

- Create: `backend/services/retrieval_service.py`
- Create: `backend/tests/test_retrieval_service.py`
- Modify: `backend/services/chat_service.py`

**Interfaces:**

- Produces: `RetrievalService.retrieve(question: str, doc_ids: list[str], top_k: int) -> list[dict]`
- Produces: `RetrievalService.build_context(results: list[dict]) -> str`
- Produces: `RetrievalService.build_citations(results: list[dict]) -> list[Citation]`

- [ ] **Step 1: Add failing tests**

Create `backend/tests/test_retrieval_service.py` with tests for:

1. Context includes numbered source markers.
2. Citations preserve `doc_id`, `doc_name`, `page`, `content`, and `relevance_score`.
3. Empty retrieval produces an empty context and citation list.

- [ ] **Step 2: Run failing tests**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_retrieval_service -v
```

Expected: FAIL because `RetrievalService` does not exist.

- [ ] **Step 3: Implement RetrievalService**

Create methods using existing `VectorStoreService.search()` and move context/citation formatting out of `ChatService`.

- [ ] **Step 4: Refactor ChatService**

Replace `_build_context` and `_build_citations` calls with `RetrievalService`. Keep the API response and stream event names unchanged.

- [ ] **Step 5: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_retrieval_service -v
```

```powershell
git add backend/services/retrieval_service.py backend/services/chat_service.py backend/tests/test_retrieval_service.py
git commit -m "feat: extract retrieval service"
```

## Task 2: Workbench Modes

**Files:**

- Modify: `backend/models/chat.py`
- Modify: `backend/services/chat_service.py`
- Create: `backend/tests/test_prompt_modes.py`
- Modify: `frontend/src/components/ChatInterface.tsx`

**Interfaces:**

- Produces backend model field: `ChatRequest.mode: Literal["review", "paper", "knowledge_base"] = "knowledge_base"`
- Produces frontend state: `chatMode`

- [ ] **Step 1: Add prompt mode tests**

Create tests asserting:

1. `review` prompt asks for study explanation and review questions.
2. `paper` prompt asks for claims, evidence, counterpoints, and citation anchors.
3. `knowledge_base` prompt asks for direct source-grounded answers.

- [ ] **Step 2: Extend ChatRequest**

Add `mode` to `backend/models/chat.py` with default `"knowledge_base"`.

- [ ] **Step 3: Add prompt mode builder**

Add `ChatService._mode_instructions(mode: str) -> str` and include it in the system prompt.

- [ ] **Step 4: Add UI segmented control**

In `ChatInterface.tsx`, add mode buttons near the input:

1. Review
2. Paper
3. Knowledge Base

Send `mode` in both `chatApi.ask()` and `chatApi.createStreamRequest()` payloads.

- [ ] **Step 5: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_prompt_modes -v
```

```powershell
cd frontend
npm run build
```

```powershell
git add backend/models/chat.py backend/services/chat_service.py backend/tests/test_prompt_modes.py frontend/src/components/ChatInterface.tsx frontend/src/services/api.ts
git commit -m "feat: add workbench answer modes"
```

## Task 3: Structure-Aware Chunk Metadata

**Files:**

- Modify: `backend/services/document_parser.py`
- Modify: `backend/services/vector_store.py`
- Modify: `backend/models/document.py`
- Create: `backend/tests/test_document_parser.py`

**Interfaces:**

- Produces: `DocumentParser.chunk_text(text: str) -> list[dict]`
- Chunk dict shape: `{"content": str, "section": str | None, "chunk_index": int}`

- [ ] **Step 1: Add parser tests**

Test that markdown headings and repeated blank lines create chunks with section names.

- [ ] **Step 2: Update parser**

Return structured chunk dictionaries instead of only raw strings. Preserve compatibility by having document processing pass `chunk["content"]` to embedding.

- [ ] **Step 3: Update vector metadata**

Store `section`, `chunk_index`, `doc_id`, and `doc_name` in ChromaDB metadata.

- [ ] **Step 4: Update citations**

Use `section` in citations when page is unavailable.

- [ ] **Step 5: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_document_parser -v
```

```powershell
git add backend/services/document_parser.py backend/services/vector_store.py backend/models/document.py backend/tests/test_document_parser.py
git commit -m "feat: preserve chunk structure metadata"
```

## Task 4: Query Rewriting And Reranking

**Files:**

- Modify: `backend/services/retrieval_service.py`
- Modify: `backend/core/config.py`
- Create: `backend/tests/test_retrieval_ranking.py`

**Interfaces:**

- Produces: `RetrievalService.rewrite_query(question: str, history: list[dict]) -> str`
- Produces: `RetrievalService.rerank(question: str, results: list[dict]) -> list[dict]`

- [ ] **Step 1: Add deterministic ranking tests**

Use fake retrieval results and assert:

1. Exact title/section matches move upward.
2. Empty results stay empty.
3. Reranked results preserve citation fields.

- [ ] **Step 2: Implement local reranking**

Use a lightweight score blend:

```text
final_score = vector_score + title_match_bonus + section_match_bonus + exact_term_bonus
```

Do not add a new model dependency in this phase.

- [ ] **Step 3: Implement optional query rewriting**

Use LLM query rewriting only when `ENABLE_QUERY_REWRITE=true` in `.env`. If disabled or failed, use the original question.

- [ ] **Step 4: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_retrieval_ranking -v
```

```powershell
git add backend/services/retrieval_service.py backend/core/config.py backend/tests/test_retrieval_ranking.py
git commit -m "feat: add query rewrite and local reranking"
```

## Task 5: Evaluation Harness

**Files:**

- Create: `backend/evals/quality_cases.json`
- Create: `backend/evals/run_quality_eval.py`
- Create: `backend/tests/test_quality_eval_schema.py`

**Interfaces:**

- Produces command: `.\venv\Scripts\python.exe evals\run_quality_eval.py --cases evals\quality_cases.json`

- [ ] **Step 1: Add eval schema test**

Require each case to include:

```json
{
  "case_id": "course-review-1",
  "question": "What is the main claim?",
  "doc_ids": [],
  "mode": "review",
  "must_cite": true,
  "expected_terms": ["claim"]
}
```

- [ ] **Step 2: Add initial eval cases**

Create 3 cases:

1. Student review.
2. Paper outline.
3. Company knowledge-base factual lookup.

Use empty `doc_ids` for initial schema-only cases. Local evaluation runs must replace them with real uploaded document IDs before answer-quality scoring.

- [ ] **Step 3: Add eval runner**

Runner loads cases, calls the local chat service, and prints JSON lines with `case_id`, `ok`, `missing_terms`, and `citation_count`.

- [ ] **Step 4: Verify and commit**

```powershell
cd backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest tests.test_quality_eval_schema -v
```

```powershell
git add backend/evals/quality_cases.json backend/evals/run_quality_eval.py backend/tests/test_quality_eval_schema.py
git commit -m "test: add answer quality eval harness"
```

## Task 6: Phase Verification

- [ ] **Step 1: Run global verification commands from the roadmap index**

- [ ] **Step 2: Manual acceptance**

Use real documents and confirm:

1. Review mode produces study-oriented output.
2. Paper mode produces claims/evidence/counterpoints.
3. Knowledge Base mode produces concise source-grounded answers.
4. Citations match relevant source snippets.
5. Repeated questions over the same source set are stable enough for demo use.

- [ ] **Step 3: Push**

```powershell
git status -sb
git push
```

## Done Criteria

Phase 3 is complete when:

1. Retrieval has its own service boundary.
2. Workbench modes affect prompt behavior.
3. Chunk metadata includes useful section/page context.
4. Reranking improves top-source ordering without new heavyweight dependencies.
5. A small evaluation harness exists and passes schema tests.
6. Global verification commands pass.
