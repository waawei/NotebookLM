# Safe LLM Connection Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Return a short-lived, structured, sanitized explanation when a Settings Chat Completions connection test fails.

**Architecture:** A focused backend diagnostic module classifies OpenAI SDK exceptions and extracts only a permitted provider message before redacting secrets, URLs, and control characters. The existing Settings test endpoint returns the typed diagnostic only on failure; the Settings React component renders it inside an expandable details section from component state.

**Tech Stack:** Python 3, FastAPI, Pydantic, OpenAI Python SDK, httpx, React 18, TypeScript, Vitest, Testing Library.

## Global Constraints

- Never return, persist, log, display, or commit an API key, authorization value, Base URL, request path, raw response body, stack trace, or exception object.
- Diagnostic data is returned only by POST /api/settings/test-llm, exists only in the current Settings component state, and is never written to localStorage, sessionStorage, Zustand, SQLite, Agent records, logs, or Git-tracked files.
- Keep the current generic connection failure message. Do not change model-discovery failure behavior or Agent-run persistence/errors.
- Diagnostic phase is chat_completion. Category is one of authentication_failed, permission_denied, model_not_found, invalid_request, rate_limited, upstream_unavailable, connection_failed, timed_out, or unknown.
- Summary removes URLs, Bearer tokens, current API keys, key-like values, and control characters, then limits output to 280 Unicode characters.
- Write a failing production-behavior test before each implementation change, run focused verification, and commit each independently working task.

---

## File Structure

- Create: backend/services/llm_diagnostics.py — exception classification, safe provider-message extraction, and summary sanitization.
- Create: backend/tests/test_llm_diagnostics.py — category/status/redaction/truncation behavior tests.
- Modify: backend/api/settings.py — typed diagnostic response model and failed test-connection result.
- Modify: backend/tests/test_settings_api.py — response-schema and secret-boundary test.
- Modify: frontend/src/services/api.ts — diagnostic TypeScript contract.
- Modify: frontend/src/components/LLMSettingsPanel.tsx — expandable safe details in the existing feedback component.
- Modify: frontend/src/views/SettingsView.test.tsx — display/clearing/no-browser-storage test.

### Task 1: Classify and sanitize LLM connection failures

**Files:**

- Create: backend/services/llm_diagnostics.py
- Create: backend/tests/test_llm_diagnostics.py

**Interfaces:**

- Produces: build_connection_diagnostic(error: Exception, api_key: str) -> dict[str, str | int | None].
- Produces: sanitize_connection_summary(value: str, api_key: str, limit: int = 280) -> str.
- Consumes: OpenAI APIStatusError, AuthenticationError, PermissionDeniedError, NotFoundError, BadRequestError, RateLimitError, InternalServerError, APIConnectionError, and APITimeoutError.

- [ ] **Step 1: Write failing classification and redaction tests**

~~~python
def test_rate_limit_diagnostic_exposes_status_and_redacts_provider_message(self):
    error = RateLimitError(
        "request failed",
        response=httpx.Response(429, request=httpx.Request("POST", "https://gateway.test/v1/chat/completions")),
        body={"error": {"message": "Bearer saved-secret at https://gateway.test/reset?token=sk-abcdefghijk"}},
    )

    diagnostic = build_connection_diagnostic(error, "saved-secret")

    self.assertEqual(diagnostic["phase"], "chat_completion")
    self.assertEqual(diagnostic["status_code"], 429)
    self.assertEqual(diagnostic["category"], "rate_limited")
    self.assertNotIn("saved-secret", diagnostic["summary"])
    self.assertNotIn("gateway.test", diagnostic["summary"])
    self.assertNotIn("sk-abcdefghijk", diagnostic["summary"])

def test_timeout_has_no_status_and_unknown_error_never_exposes_text(self):
    timeout = APITimeoutError(request=httpx.Request("POST", "https://gateway.test/v1/chat/completions"))
    self.assertEqual(build_connection_diagnostic(timeout, "")["category"], "timed_out")
    self.assertIsNone(build_connection_diagnostic(timeout, "")["status_code"])
    self.assertEqual(build_connection_diagnostic(RuntimeError("secret"), "secret")["summary"], "No safe upstream summary was available.")
~~~

- [ ] **Step 2: Run tests to verify RED**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_llm_diagnostics -v

Expected: import failure because llm_diagnostics does not exist.

- [ ] **Step 3: Implement the minimum backend module**

~~~python
def build_connection_diagnostic(error: Exception, api_key: str) -> dict[str, str | int | None]:
    category, default_summary = _classify(error)
    status_code = getattr(error, "status_code", None)
    provider_message = _provider_message(error)
    summary = sanitize_connection_summary(provider_message or default_summary, api_key)
    return {
        "phase": "chat_completion",
        "status_code": status_code if isinstance(status_code, int) else None,
        "category": category,
        "summary": summary,
    }
~~~

Implement _classify with the exact category mapping in Global Constraints, checking APITimeoutError before APIConnectionError and RateLimitError before generic APIStatusError. _provider_message may read only body.error.message or body.message when they are strings; it returns an empty string for other body shapes and all unknown exceptions. sanitize_connection_summary must redact the supplied API key, a case-insensitive Bearer token value, all http/https URLs, sk-/rk-/key- values with at least eight following non-whitespace characters, CR/LF/tab characters, then normalize whitespace and truncate to 280 characters.

- [ ] **Step 4: Verify GREEN**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_llm_diagnostics -v; .\venv\Scripts\python.exe -m py_compile services/llm_diagnostics.py

Expected: all tests pass and no test output includes fixture secret values.

- [ ] **Step 5: Commit**

~~~powershell
git add backend/services/llm_diagnostics.py backend/tests/test_llm_diagnostics.py
git commit -m "feat: classify safe LLM connection diagnostics"
~~~

### Task 2: Return the typed diagnostic only from failed connection tests

**Files:**

- Modify: backend/api/settings.py
- Modify: backend/tests/test_settings_api.py

**Interfaces:**

- Consumes: build_connection_diagnostic(error, configuration_service.effective_config().api_key).
- Produces: LLMConnectionDiagnostic(phase: str, status_code: int | None, category: str, summary: str).
- Produces: LLMTestResult(ok: bool, message: str, diagnostic: LLMConnectionDiagnostic | None = None).

- [ ] **Step 1: Write a failing Settings API test**

~~~python
def test_connection_failure_returns_only_a_safe_typed_diagnostic(self):
    settings.LLMService = RateLimitedLLMService

    result = asyncio.run(settings.test_llm_connection())

    self.assertFalse(result.ok)
    self.assertEqual(result.diagnostic.phase, "chat_completion")
    self.assertEqual(result.diagnostic.status_code, 429)
    self.assertEqual(result.diagnostic.category, "rate_limited")
    self.assertNotIn("saved-secret", result.model_dump_json())
    self.assertNotIn("gateway.test", result.model_dump_json())
~~~

RateLimitedLLMService.test_connection raises a real RateLimitError whose response body includes saved-secret and a gateway URL.

- [ ] **Step 2: Run test to verify RED**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_settings_api -v

Expected: result has no diagnostic field.

- [ ] **Step 3: Implement the minimum API change**

~~~python
class LLMConnectionDiagnostic(BaseModel):
    phase: str
    status_code: Optional[int]
    category: str
    summary: str

class LLMTestResult(BaseModel):
    ok: bool
    message: str
    diagnostic: Optional[LLMConnectionDiagnostic] = None

@router.post("/test-llm", response_model=LLMTestResult)
async def test_llm_connection():
    config = configuration_service.effective_config()
    try:
        await LLMService(config).test_connection()
        return LLMTestResult(ok=True, message="LLM connection succeeded")
    except Exception as error:
        return LLMTestResult(
            ok=False,
            message="LLM connection failed. Check provider, model, endpoint, and API key.",
            diagnostic=LLMConnectionDiagnostic(**build_connection_diagnostic(error, config.api_key)),
        )
~~~

Keep the existing warning pre-check. Do not log the caught error and do not attach it as an exception cause.

- [ ] **Step 4: Verify GREEN**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_llm_diagnostics tests.test_settings_api -v; .\venv\Scripts\python.exe -m py_compile api/settings.py

Expected: all tests pass; both successful and warning results have diagnostic null or omitted; only failure returns the safe schema.

- [ ] **Step 5: Commit**

~~~powershell
git add backend/api/settings.py backend/tests/test_settings_api.py
git commit -m "feat: return safe connection diagnostics"
~~~

### Task 3: Render and clear connection details in Settings

**Files:**

- Modify: frontend/src/services/api.ts
- Modify: frontend/src/components/LLMSettingsPanel.tsx
- Modify: frontend/src/views/SettingsView.test.tsx

**Interfaces:**

- Produces: SettingsConnectionDiagnostic and SettingsTestResult.diagnostic?: SettingsConnectionDiagnostic | null.
- Consumes: settingsApi.testLlm() result.
- Produces: a Details section labelled Connection details, shown only for a failed result with a diagnostic.

- [ ] **Step 1: Write failing Settings view tests**

~~~tsx
it('renders a safe connection diagnostic and never writes it to storage', async () => {
  const diagnostic = { phase: 'chat_completion', status_code: 429, category: 'rate_limited', summary: 'The upstream request was rate limited.' }
  const setItem = vi.spyOn(Storage.prototype, 'setItem')
  settingsApiMock.testLlm.mockResolvedValue({ ok: false, message: 'LLM connection failed. Check provider, model, endpoint, and API key.', diagnostic })

  render(<SettingsView />)
  await screen.findByText('Runtime settings')
  fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

  expect(await screen.findByText('Connection details')).toBeInTheDocument()
  expect(screen.getByText('HTTP status')).toBeInTheDocument()
  expect(screen.getByText('429')).toBeInTheDocument()
  expect(setItem).not.toHaveBeenCalled()
  setItem.mockRestore()
})

it('clears connection details before a retry', async () => {
  settingsApiMock.testLlm
    .mockResolvedValueOnce({ ok: false, message: 'LLM connection failed. Check provider, model, endpoint, and API key.', diagnostic })
    .mockResolvedValueOnce({ ok: true, message: 'LLM connection succeeded' })

  render(<SettingsView />)
  await screen.findByText('Runtime settings')
  fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))
  await screen.findByText('Connection details')
  fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

  await waitFor(() => expect(screen.queryByText('Connection details')).not.toBeInTheDocument())
})
~~~

- [ ] **Step 2: Run tests to verify RED**

Run: cd frontend; npm run test -- --run src/views/SettingsView.test.tsx

Expected: diagnostic is not typed or Connection details is absent.

- [ ] **Step 3: Implement the minimum client and UI behavior**

~~~ts
export interface SettingsConnectionDiagnostic {
  phase: 'chat_completion'
  status_code: number | null
  category: string
  summary: string
}

export interface SettingsTestResult {
  ok: boolean
  message: string
  diagnostic?: SettingsConnectionDiagnostic | null
}
~~~

In Feedback, render only when !message.ok and message.diagnostic:

~~~tsx
<details className="mt-3 border-t pt-3">
  <summary>Connection details</summary>
  <dl>
    <div><dt>Request phase</dt><dd>{message.diagnostic.phase}</dd></div>
    {message.diagnostic.status_code !== null && <div><dt>HTTP status</dt><dd>{message.diagnostic.status_code}</dd></div>}
    <div><dt>Category</dt><dd>{message.diagnostic.category}</dd></div>
    <div><dt>Summary</dt><dd>{message.diagnostic.summary}</dd></div>
  </dl>
</details>
~~~

Continue clearing message with setMessage(null) at the start of loadStatus, saveConfiguration, clearConfiguration, testConnection, and loadModels. Do not add any storage, global store, logging, toast history, or routing behavior.

- [ ] **Step 4: Verify GREEN**

Run: cd frontend; npm run test -- --run src/services/api.test.ts src/views/SettingsView.test.tsx; npm run build

Expected: tests pass, the component has no storage write, and TypeScript/build exit 0.

- [ ] **Step 5: Commit**

~~~powershell
git add frontend/src/services/api.ts frontend/src/components/LLMSettingsPanel.tsx frontend/src/views/SettingsView.test.tsx
git commit -m "feat: show safe connection diagnostics"
~~~

### Task 4: Full regression and manual diagnostic acceptance

**Files:** Modify only after a failing regression test demonstrates a defect.

- [ ] **Step 1: Run all required automated verification**

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

- [ ] **Step 2: Perform safe manual acceptance**

Use an unsupported model, an invalid key, or a known rate-limited connection. Confirm that the Settings failure contains the fixed message plus Details with chat_completion, a category, status code when available, and a short summary. Confirm that no visible value contains the configured key, an Authorization/Bearer value, Base URL, request path, query string, or raw provider response. Retry, refresh, save, clear, and load models; confirm Details is cleared.

- [ ] **Step 3: Commit only demonstrated regression fixes**

~~~powershell
git status --short
git add <affected-files>
git commit -m "fix: <demonstrated diagnostic defect>"
~~~

## Plan Self-Review

- Spec coverage: Task 1 provides exact mappings and sanitization; Task 2 limits the API contract to failed connection tests; Task 3 limits display to Settings component memory; Task 4 verifies all security and regression requirements.
- Placeholder scan: Every task names concrete files, interfaces, tests, commands, expected behavior, and commit boundaries.
- Type consistency: build_connection_diagnostic, LLMConnectionDiagnostic, SettingsConnectionDiagnostic, and SettingsTestResult.diagnostic use matching phase/status/category/summary fields.

