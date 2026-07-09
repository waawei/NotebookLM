# Endpoint Modes and Model Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Let a local user use predictable OpenAI-compatible endpoints and discover models from saved or one-time credentials without persisting or exposing API keys.

**Architecture:** Extend the backend-local overlay with a non-secret endpoint_mode, resolve temporary patches through LLMConfigurationService.preview, and have LLMService normalize only its client base URL. The Settings API exposes a fixed safe discovery operation; React keeps temporary keys and returned IDs only in component state.

**Tech Stack:** Python 3, FastAPI, Pydantic, OpenAI SDK, React 18, TypeScript, TailwindCSS, Vitest, Testing Library.

## Global Constraints

- Never persist, log, return, display, serialize, or commit an API key. A temporary key exists only in a model-discovery request body and ephemeral backend configuration.
- Endpoint mode is exactly auto or exact, has no secret value, and may appear in safe status.
- Automatic strips trailing slashes and appends /v1 exactly once; exact strips trailing slashes and never appends it.
- OpenAI may use its default endpoint with an empty Base URL; openai_compatible requires HTTP(S) Base URL; DashScope retains its built-in endpoint.
- Discovery returns only sorted/deduplicated/non-empty model IDs and fixed safe failures; never upstream bodies or exception strings.
- Browser requests must use frontend/src/services/api.ts; manual model input must continue to work.
- Write a failing production test before each code change, run focused verification, and commit each independent deliverable.

---

## File Structure

- backend/services/local_llm_config.py: EndpointMode, persistence/validation, safe status, preview merge.
- backend/services/llm_service.py: mode-aware client URL normalization and model listing.
- backend/api/settings.py: discovery request/response and fixed-failure endpoint.
- backend/tests/test_local_llm_config.py, backend/tests/test_llm_service.py, backend/tests/test_settings_api.py: backend tests.
- frontend/src/services/api.ts, frontend/src/services/api.test.ts: frontend request types/method coverage.
- frontend/src/components/LLMSettingsPanel.tsx, frontend/src/views/SettingsView.test.tsx: form interaction and tests.

### Task 1: Resolve and persist non-secret endpoint mode

**Files:**

- Modify: backend/services/local_llm_config.py
- Modify: backend/tests/test_local_llm_config.py

**Interfaces:**

- Produces: EndpointMode = Literal["auto", "exact"].
- Produces: EffectiveLLMConfig(..., endpoint_mode: EndpointMode).
- Produces: LLMConfigurationService.preview(values: dict) -> EffectiveLLMConfig.
- Produces: safe_status()["endpoint_mode"].

- [ ] **Step 1: Write the failing tests**

~~~python
def test_preview_merges_a_temporary_key_without_writing_the_overlay(self):
    service = self.make_service()
    preview = service.preview({"provider": "openai_compatible", "model": "listed", "base_url": "https://gateway.test", "api_key": "temporary-key", "endpoint_mode": "exact"})
    self.assertEqual(preview.api_key, "temporary-key")
    self.assertEqual(preview.endpoint_mode, "exact")
    self.assertFalse(self.path.exists())

def test_safe_status_returns_endpoint_mode_but_never_key(self):
    service = self.make_service()
    service.save({"provider": "openai", "model": "listed", "api_key": "stored-key", "endpoint_mode": "exact"})
    self.assertEqual(service.safe_status()["endpoint_mode"], "exact")
    self.assertNotIn("stored-key", str(service.safe_status()))
~~~

- [ ] **Step 2: Verify RED**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_local_llm_config -v

Expected: failure because preview and endpoint_mode do not exist.

- [ ] **Step 3: Implement the minimum**

~~~python
EndpointMode = Literal["auto", "exact"]

def preview(self, values: dict) -> EffectiveLLMConfig:
    candidate = self._merge(values)
    self._validate(candidate)
    return self._to_effective_config(candidate)
~~~

Use the same merge path for saved effective configuration. Permit only provider, model, base_url, api_key, and endpoint_mode; default mode to auto; reject other modes; persist only the non-secret mode; include only its name in safe status.

- [ ] **Step 4: Verify GREEN**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_local_llm_config -v; .\venv\Scripts\python.exe -m py_compile services/local_llm_config.py

Expected: tests pass and compilation exits 0.

- [ ] **Step 5: Commit**

~~~powershell
git add backend/services/local_llm_config.py backend/tests/test_local_llm_config.py
git commit -m "feat: resolve endpoint modes safely"
~~~

### Task 2: Normalize base URLs and obtain model IDs

**Files:**

- Modify: backend/services/llm_service.py
- Modify: backend/tests/test_llm_service.py

**Interfaces:**

- Produces: normalize_openai_base_url(base_url: str, endpoint_mode: EndpointMode = "auto") -> str.
- Produces: LLMService.list_models() -> list[str].

- [ ] **Step 1: Write the failing tests**

~~~python
def test_exact_mode_does_not_append_v1(self):
    self.assertEqual(normalize_openai_base_url("https://gateway.test/custom/", "exact"), "https://gateway.test/custom")

def test_auto_mode_accepts_root_slash_and_v1_forms(self):
    for value in ("https://gateway.test", "https://gateway.test/", "https://gateway.test/v1", "https://gateway.test/v1/"):
        self.assertEqual(normalize_openai_base_url(value, "auto"), "https://gateway.test/v1")

def test_list_models_returns_sorted_unique_non_empty_ids(self):
    service = LLMService(self.config)
    service.client = FakeClient(["z-model", "", "a-model", "z-model"])
    self.assertEqual(service.list_models(), ["a-model", "z-model"])
~~~

- [ ] **Step 2: Verify RED**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_llm_service -v

Expected: mode argument/listing function is missing.

- [ ] **Step 3: Implement the minimum**

~~~python
def normalize_openai_base_url(base_url: str, endpoint_mode: EndpointMode = "auto") -> str:
    normalized = base_url.rstrip("/")
    if not normalized or endpoint_mode == "exact":
        return normalized
    return normalized if normalized.endswith("/v1") else f"{normalized}/v1"

def list_models(self) -> list[str]:
    ids = [getattr(item, "id", "") for item in self._get_client().models.list().data]
    return sorted({item for item in ids if isinstance(item, str) and item})
~~~

Pass EffectiveLLMConfig.endpoint_mode to OpenAI/openai-compatible URL normalization. Do not log or wrap upstream exceptions in this service.

- [ ] **Step 4: Verify GREEN**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_llm_service -v; .\venv\Scripts\python.exe -m py_compile services/llm_service.py

Expected: tests pass and compilation exits 0.

- [ ] **Step 5: Commit**

~~~powershell
git add backend/services/llm_service.py backend/tests/test_llm_service.py
git commit -m "feat: normalize endpoints and list models"
~~~

### Task 3: Discover models from a non-persisting configuration preview

**Files:**

- Modify: backend/api/settings.py
- Modify: backend/tests/test_settings_api.py

**Interfaces:**

- Produces: LLMModelDiscoveryRequest(provider: str | None, base_url: str | None, api_key: str | None, endpoint_mode: str | None).
- Produces: LLMModelDiscoveryResult(models: list[str]).
- Produces: POST /api/settings/models handled by list_llm_models.

- [ ] **Step 1: Write the failing endpoint tests**

~~~python
def test_model_discovery_uses_preview_and_returns_only_ids(self):
    settings.LLMService = ListingLLMService
    response = asyncio.run(settings.list_llm_models(settings.LLMModelDiscoveryRequest(api_key="temporary-key")))
    self.assertEqual(response.models, ["a-model", "z-model"])
    self.assertEqual(self.configuration_service.previewed["api_key"], "temporary-key")
    self.assertNotIn("temporary-key", str(response))

def test_model_discovery_hides_upstream_failure(self):
    settings.LLMService = RaisingLLMService
    with self.assertRaisesRegex(HTTPException, "Unable to load available models"):
        asyncio.run(settings.list_llm_models(settings.LLMModelDiscoveryRequest(api_key="temporary-key")))
~~~

- [ ] **Step 2: Verify RED**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_settings_api -v

Expected: request model and handler are missing.

- [ ] **Step 3: Implement the minimum**

~~~python
@router.post("/models", response_model=LLMModelDiscoveryResult)
async def list_llm_models(request: LLMModelDiscoveryRequest):
    try:
        config = configuration_service.preview(request.model_dump(exclude_none=True))
        return LLMModelDiscoveryResult(models=LLMService(config).list_models())
    except (ValueError, OpenAIError) as exc:
        raise HTTPException(status_code=400, detail="Unable to load available models. Check the provider, endpoint, and API key.") from exc
~~~

Catch the configured OpenAI/client request exception family and ValueError with exactly that fixed detail. Preview must never invoke save.

- [ ] **Step 4: Verify GREEN**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_settings_api -v; .\venv\Scripts\python.exe -m py_compile api/settings.py

Expected: tests pass and no response contains fixture secrets.

- [ ] **Step 5: Commit**

~~~powershell
git add backend/api/settings.py backend/tests/test_settings_api.py
git commit -m "feat: discover models from temporary settings"
~~~

### Task 4: Make the form clear, temporary, and discoverable

**Files:**

- Modify: frontend/src/services/api.ts
- Modify: frontend/src/services/api.test.ts
- Modify: frontend/src/components/LLMSettingsPanel.tsx
- Modify: frontend/src/views/SettingsView.test.tsx

**Interfaces:**

- Produces: SettingsStatus.endpoint_mode, SettingsConfigUpdate.endpoint_mode, SettingsModelDiscoveryRequest, and settingsApi.listModels(data).
- Produces: controls labelled Endpoint format, Show API key, and Load available models.

- [ ] **Step 1: Write the failing UI/client tests**

~~~tsx
it('uses the temporary typed key only for model discovery and clears it afterwards', async () => {
  settingsApi.listModels.mockResolvedValue({ models: ['a-model'] })
  render(<SettingsView />)
  await user.type(screen.getByLabelText('API key'), 'temporary-browser-key')
  await user.click(screen.getByRole('button', { name: 'Load available models' }))
  await waitFor(() => expect(settingsApi.listModels).toHaveBeenCalledWith(expect.objectContaining({ api_key: 'temporary-browser-key' })))
  expect(screen.getByLabelText('API key')).toHaveValue('')
  expect(screen.getByRole('option', { name: 'a-model' })).toBeInTheDocument()
})

it('shows an API key only while the current form field is toggled', async () => {
  render(<SettingsView />)
  await user.type(screen.getByLabelText('API key'), 'current-value')
  await user.click(screen.getByRole('button', { name: 'Show API key' }))
  expect(screen.getByLabelText('API key')).toHaveAttribute('type', 'text')
})
~~~

- [ ] **Step 2: Verify RED**

Run: cd frontend; npm run test -- --run src/services/api.test.ts src/views/SettingsView.test.tsx

Expected: discovery method and controls are missing.

- [ ] **Step 3: Implement the minimum**

~~~ts
export interface SettingsModelDiscoveryRequest {
  provider?: string
  base_url?: string
  api_key?: string
  endpoint_mode?: 'auto' | 'exact'
}

listModels: async (data) => (await api.post('/settings/models', data)).data,
~~~

Keep endpointMode, showApiKey, isLoadingModels, and models in local component state. Set the API-key input to text only after its eye control is clicked. On discovery include typed URL only if touched and key only if non-empty; clear key in finally. Attach returned IDs to a datalist without blocking free entry. Explain automatic root versus /v1, exact documented API bases, and that /models or /chat/completions are not Base URL values. Use fixed error copy and no storage calls.

- [ ] **Step 4: Verify GREEN**

Run: cd frontend; npm run test -- --run src/services/api.test.ts src/views/SettingsView.test.tsx; npm run build

Expected: tests pass and build exits 0.

- [ ] **Step 5: Commit**

~~~powershell
git add frontend/src/services/api.ts frontend/src/services/api.test.ts frontend/src/components/LLMSettingsPanel.tsx frontend/src/views/SettingsView.test.tsx
git commit -m "feat: guide endpoints and discover models"
~~~

### Task 5: Regression and acceptance verification

**Files:** Modify only after demonstrating a defect with a failing regression test.

- [ ] **Step 1: Run automated checks**

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

- [ ] **Step 2: Perform manual safe acceptance**

Enter a compatible relay root URL and unsaved key, load models, then repeat using /v1/ and exact mode. Confirm returned models are selectable and manual typing remains possible; the key is hidden by default, may be revealed only while editing, clears after discovery/save/test, and never appears in status/errors/browser storage/Agent records/logs/Git status.

- [ ] **Step 3: Commit only demonstrated regression fixes**

~~~powershell
git status --short
git add <affected-files>
git commit -m "fix: <demonstrated discovery defect>"
~~~

## Plan Self-Review

- Spec coverage: Tasks 1–4 implement every approved endpoint, temporary-key, API, help, and model-list requirement. Task 5 verifies the security boundary and full build/test/compile result.
- Placeholder scan: Every task gives concrete files, interfaces, test code, commands, expected behavior, and commit scope.
- Type consistency: EndpointMode, EffectiveLLMConfig.endpoint_mode, preview, list_models, LLMModelDiscoveryRequest, and settingsApi.listModels use one contract throughout.

