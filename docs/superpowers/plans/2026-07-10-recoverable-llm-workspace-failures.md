# Recoverable LLM Workspace Failures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Apply current local LLM settings to every new workspace generation and render safe, recoverable summary/chat failures rather than misleading or blank UI states.

**Architecture:** Extend document metadata with non-secret summary state and migrate legacy sentinel summaries. Resolve LLMService through injected factories at each generation boundary. Reuse the existing diagnostic builder for a typed chat SSE error, while React keeps streaming diagnostics in component state and persists only a generic assistant failure string.

**Tech Stack:** Python 3, FastAPI, Pydantic, SQLite, OpenAI Python SDK, React 18, TypeScript, Zustand, Vitest, Testing Library.

## Global Constraints

- Never return, persist, log, or commit API keys, Base URLs, request paths, raw upstream bodies, exception objects, stack traces, or diagnostics.
- No local fallback answer, extractive summary, or fabricated content may be generated when LLM generation fails.
- A completed document means parsing, chunking, and vector indexing completed; an unavailable LLM summary must be represented separately.
- New chat, stream, suggested-question, and summary work must use the current backend configuration without a restart.
- Browser requests must use frontend/src/services/api.ts. Diagnostics remain component-local and never enter localStorage, sessionStorage, Zustand persistence, SQLite, Agent records, URLs, or toast history.
- Model-discovery and Agent-run behavior remain unchanged.
- Write a failing production-behavior test before every implementation change, run focused verification, and commit each independent deliverable.

---

## File Structure

- Modify: backend/models/document.py — non-secret summary state in document responses.
- Modify: backend/services/document_metadata_store.py — SQLite columns, migration, and update methods.
- Modify: backend/services/document_service.py — per-operation LLM factory and safe summary/processing state.
- Create: backend/tests/test_document_service.py — fresh factory and summary-state tests.
- Modify: backend/tests/test_metadata_store.py — migration/state persistence test.
- Modify: backend/services/chat_service.py — fresh LLM factory for all generation operations.
- Modify: backend/api/chat.py — typed safe streaming error event.
- Create: backend/tests/test_chat_api.py — safe SSE error and fresh chat factory tests.
- Modify: frontend/src/services/api.ts — stream error diagnostic type.
- Modify: frontend/src/components/ChatInterface.tsx — inline source recovery and safe error card.
- Modify: frontend/src/components/Sidebar.tsx — explicit selected marker and summary state.
- Modify: frontend/src/store/useStore.ts — document state fields only; do not add diagnostic persistence.
- Modify: frontend/src/components/ChatInterface.test.tsx — source/error behavior tests.
- Create: frontend/src/components/Sidebar.test.tsx — selected and summary-state display tests.

### Task 1: Persist truthful document summary state and use a fresh summary client

**Files:**

- Modify: backend/models/document.py
- Modify: backend/services/document_metadata_store.py
- Modify: backend/services/document_service.py
- Modify: backend/tests/test_metadata_store.py
- Create: backend/tests/test_document_service.py

**Interfaces:**

- Produces: DocumentMetadata.summary_status: str = "pending" and summary_error: Optional[str] = None.
- Produces: DocumentResponse.summary_status and summary_error.
- Produces: DocumentMetadataStore.update_status(..., summary_status: Optional[str] = None, summary_error: Optional[str] = None).
- Produces: DocumentService(..., llm_factory: Callable[[], LLMService] | None = None).

- [ ] **Step 1: Write the failing metadata and service tests**

~~~python
def test_legacy_failed_summary_migrates_to_unavailable_without_literal_content(self):
    self.store.upsert_document(DocumentMetadata(
        doc_id="doc-1", filename="paper.pdf", file_type="pdf", file_size=1,
        upload_time="2026-07-10T00:00:00", status="completed",
        summary="Summary generation failed.",
    ))

    reopened = DocumentMetadataStore(self.db_path)
    record = reopened.get_document("doc-1")

    self.assertEqual(record["summary_status"], "unavailable")
    self.assertEqual(record["summary_error"], "LLM summary unavailable")
    self.assertIsNone(record["summary"])

async def test_summary_uses_a_new_llm_factory_and_keeps_index_completed_on_failure(self):
    factory = FakeLLMFactory([FailingLLM(), WorkingLLM("fresh summary")])
    service = DocumentService(metadata_store=self.store, parser=self.parser,
                              vector_store=self.vector_store, llm_factory=factory)
    await service.process_document("doc-1")
    self.assertEqual(self.store.get_document("doc-1")["summary_status"], "unavailable")
    self.assertEqual(factory.calls, 1)
    self.assertEqual(await service._generate_summary("source text"), "fresh summary")
    self.assertEqual(factory.calls, 2)
~~~

Fake parser returns source text, Fake vector store accepts chunks, and FailingLLM.generate raises an exception containing a fixture secret.

- [ ] **Step 2: Verify RED**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_metadata_store tests.test_document_service -v

Expected: summary_status and llm_factory are unavailable.

- [ ] **Step 3: Implement the minimum metadata migration and service behavior**

~~~python
# DocumentMetadata and DocumentResponse
summary_status: str = "pending"
summary_error: Optional[str] = None

# _init_db, after CREATE TABLE
self._ensure_document_column(conn, "summary_status", "TEXT NOT NULL DEFAULT 'pending'")
self._ensure_document_column(conn, "summary_error", "TEXT")
conn.execute(
    "UPDATE documents SET summary = NULL, summary_status = 'unavailable', "
    "summary_error = 'LLM summary unavailable' "
    "WHERE summary = 'Summary generation failed.'"
)
conn.execute(
    "UPDATE documents SET summary_status = 'available' "
    "WHERE summary_status = 'pending' AND summary IS NOT NULL"
)
~~~

Implement _ensure_document_column with PRAGMA table_info(documents), adding only a missing column. Extend upsert_document and update_status to round-trip summary_state fields. In DocumentService, use self.llm_factory() inside _generate_summary. Return a tuple (summary, summary_status, summary_error): success is (trimmed_summary, "available", None); an LLM failure is (None, "unavailable", "LLM summary unavailable"). Keep completed after indexing succeeds. In outer processing failures, store only error_message "Document processing failed" and summary_status "pending", never str(error).

- [ ] **Step 4: Verify GREEN**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_metadata_store tests.test_document_service -v; .\venv\Scripts\python.exe -m py_compile models/document.py services/document_metadata_store.py services/document_service.py

Expected: all tests pass; fixture secret is absent from stored records.

- [ ] **Step 5: Commit**

~~~powershell
git add backend/models/document.py backend/services/document_metadata_store.py backend/services/document_service.py backend/tests/test_metadata_store.py backend/tests/test_document_service.py
git commit -m "feat: preserve indexed documents without summaries"
~~~

### Task 2: Use fresh chat clients and emit safe streaming failures

**Files:**

- Modify: backend/services/chat_service.py
- Modify: backend/api/chat.py
- Create: backend/tests/test_chat_api.py

**Interfaces:**

- Produces: ChatService(..., llm_factory: Callable[[], LLMService] | None = None).
- Produces: SSE error event {type, message, diagnostic}.
- Consumes: build_connection_diagnostic(error, LLMConfigurationService().effective_config().api_key).

- [ ] **Step 1: Write failing factory and SSE tests**

~~~python
async def test_each_chat_generation_uses_a_fresh_factory(self):
    factory = FakeLLMFactory([FakeLLM("first"), FakeLLM("second")])
    service = ChatService(retrieval_service=FakeRetrieval(), metadata_store=self.store, llm_factory=factory)

    await service.ask("question", ["doc-1"])
    await service.ask("question", ["doc-1"])

    self.assertEqual(factory.calls, 2)

async def test_stream_error_contains_only_safe_diagnostic_fields(self):
    chat.chat_service = FailingChatService()
    response = await chat.ask_question_stream(ChatRequest(question="question", doc_ids=["doc-1"]))
    payload = await first_sse_payload(response)

    self.assertEqual(payload["type"], "error")
    self.assertEqual(payload["diagnostic"]["status_code"], 429)
    self.assertNotIn("saved-secret", json.dumps(payload))
    self.assertNotIn("gateway.test", json.dumps(payload))
~~~

FailingChatService.ask_stream raises a RateLimitError whose body contains the fixture secret and gateway URL.

- [ ] **Step 2: Verify RED**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_chat_api -v

Expected: factory injection and diagnostic event fields are unavailable; current payload contains the raw exception message.

- [ ] **Step 3: Implement the minimum safe chat boundary**

~~~python
# ChatService generation sites
answer = await self.llm_factory().generate(prompt)
async for chunk in self.llm_factory().generate_stream(prompt):
    ...

# api/chat.py generator exception
except Exception as error:
    diagnostic = build_connection_diagnostic(
        error, LLMConfigurationService().effective_config().api_key
    )
    yield sse({"type": "error",
               "message": "The response could not be generated. Check the LLM connection in Settings and try again.",
               "diagnostic": diagnostic})
~~~

Use the same fresh-factory pattern in generate_suggested_questions. Keep conversation persistence only after successful full answers. The non-streaming chat and suggested-question handlers return fixed safe HTTP detail strings on unexpected failures; do not serialize str(error).

- [ ] **Step 4: Verify GREEN**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_chat_api tests.test_llm_diagnostics -v; .\venv\Scripts\python.exe -m py_compile services/chat_service.py api/chat.py

Expected: tests pass and no API/SSE fixture key or URL is serialized.

- [ ] **Step 5: Commit**

~~~powershell
git add backend/services/chat_service.py backend/api/chat.py backend/tests/test_chat_api.py
git commit -m "feat: return recoverable safe chat failures"
~~~

### Task 3: Render recoverable source, summary, and chat states

**Files:**

- Modify: frontend/src/services/api.ts
- Modify: frontend/src/store/useStore.ts
- Modify: frontend/src/components/ChatInterface.tsx
- Modify: frontend/src/components/Sidebar.tsx
- Modify: frontend/src/components/ChatInterface.test.tsx
- Create: frontend/src/components/Sidebar.test.tsx

**Interfaces:**

- Produces: StreamErrorEvent.diagnostic?: SettingsConnectionDiagnostic | null.
- Produces: Document.summary_status?: "pending" | "available" | "unavailable" and summary_error?: string | null.
- Produces: inline text Select at least one source before asking a question.
- Produces: details labelled Connection details only from ChatInterface local state.

- [ ] **Step 1: Write failing component tests**

~~~tsx
it('shows an inline source-selection recovery message without calling the chat API', async () => {
  render(<ChatInterface />)
  fireEvent.change(screen.getByPlaceholderText('Ask a question about your sources...'), { target: { value: 'Question' } })
  fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

  expect(await screen.findByText('Select at least one source before asking a question.')).toBeInTheDocument()
  expect(chatApi.createStreamRequest).not.toHaveBeenCalled()
})

it('replaces the optimistic assistant reply with a safe failure and local details', async () => {
  mockStream([sse({ type: 'error', message: 'The response could not be generated. Check the LLM connection in Settings and try again.', diagnostic })])
  useStore.setState({ selectedDocIds: ['doc-1'] })
  render(<ChatInterface />)
  submitQuestion('Question')

  expect(await screen.findByText('The response could not be generated. Check the LLM connection in Settings and try again.')).toBeInTheDocument()
  expect(screen.getByText('Connection details')).toBeInTheDocument()
})

it('shows indexed summary unavailability separately from processing failure', () => {
  useStore.setState({ documents: [indexedUnavailable, processingFailed] })
  render(<Sidebar isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

  expect(screen.getByText('LLM summary unavailable')).toBeInTheDocument()
  expect(screen.getByText('Processing failed')).toBeInTheDocument()
})
~~~

- [ ] **Step 2: Verify RED**

Run: cd frontend; npm run test -- --run src/components/ChatInterface.test.tsx src/components/Sidebar.test.tsx

Expected: inline selection recovery, safe error details, and truthful source labels are missing.

- [ ] **Step 3: Implement the minimum UI behavior**

~~~tsx
if (selectedDocIds.length === 0) {
  setInlineError('Select at least one source before asking a question.')
  return
}

// SSE event
if (data.type === 'error') {
  updateMessageAtIndex(tempMessageIndex, { role: 'assistant', content: data.message, citations: [] })
  setStreamDiagnostic(data.diagnostic ?? null)
  streamFailed = true
  break
}
~~~

Keep streamDiagnostic and inlineError in ChatInterface useState only; clear both before a new question. Parse errors remain console-free fixed UI errors, but must never replace or conceal a valid server error event. Render Connection details from streamDiagnostic below the generic assistant failure. In Sidebar use summary_status to display Indexed with LLM summary unavailable and error status to display Processing failed; add CheckCircle2 plus Selected text when selected. Do not add summary failure or diagnostics to Message or the Zustand persistence path.

- [ ] **Step 4: Verify GREEN**

Run: cd frontend; npm run test -- --run src/components/ChatInterface.test.tsx src/components/Sidebar.test.tsx src/services/api.test.ts; npm run build

Expected: all tests pass and no stream diagnostic is written through Storage.prototype.setItem.

- [ ] **Step 5: Commit**

~~~powershell
git add frontend/src/services/api.ts frontend/src/store/useStore.ts frontend/src/components/ChatInterface.tsx frontend/src/components/Sidebar.tsx frontend/src/components/ChatInterface.test.tsx frontend/src/components/Sidebar.test.tsx
git commit -m "feat: recover workspace generation failures"
~~~

### Task 4: Full verification and real failure acceptance

**Files:** Modify only after a demonstrated regression with a failing test.

- [ ] **Step 1: Run full automated verification**

~~~powershell
cd frontend
npm run test -- --run
npm run build
cd ..\backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest discover -s tests -v
$files = Get-ChildItem -Recurse -Include *.py | Where-Object { $_.FullName -notmatch '\\venv\\' } | ForEach-Object { $_.FullName }
.\venv\Scripts\python.exe -m py_compile @files
~~~

Expected: every command exits 0.

- [ ] **Step 2: Perform real local acceptance**

With the known unavailable upstream, upload/select a small source. Verify the document reaches indexed/completed with summary_status unavailable and no synthetic summary; ask a question and verify a visible generic assistant failure plus safe chat_completion details, never a blank response. Deselect all sources and verify the inline selection prompt without an outbound request. Save a corrected connection and verify a new chat/summary generation uses it without restarting the backend.

- [ ] **Step 3: Commit only demonstrated regression fixes**

~~~powershell
git status --short
git add <affected-files>
git commit -m "fix: <demonstrated workspace recovery defect>"
~~~

## Plan Self-Review

- Spec coverage: Task 1 implements truthful document state and fresh summary configuration; Task 2 implements fresh chat configuration and safe SSE failure; Task 3 implements all requested recovery UI; Task 4 validates automated and real failure behavior.
- Placeholder scan: Every task names exact files, interfaces, failing tests, commands, expected output, and commit scope.
- Type consistency: summary_status/summary_error, llm_factory, build_connection_diagnostic, StreamErrorEvent, and SettingsConnectionDiagnostic use matching fields throughout.

