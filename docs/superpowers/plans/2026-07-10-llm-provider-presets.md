# LLM Provider Presets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Ollama and DeepSeek provider presets to Settings while preserving the Phase 5 LLM and Agent safety boundaries.

**Architecture:** Extend the existing `LLMConfigurationService` provider validation and effective configuration resolution. Keep `LLMService` on the OpenAI SDK path because both Ollama and DeepSeek expose OpenAI-compatible chat completions. Add small UI preset behavior inside `LLMSettingsPanel` and keep all frontend HTTP calls in `frontend/src/services/api.ts`.

**Tech Stack:** Python unittest, FastAPI/Pydantic models, OpenAI Python SDK, React, Vitest, Testing Library.

## Global Constraints

- Write failing tests before production behavior changes.
- API keys must remain write-only and must not appear in API responses, frontend storage, SQLite Agent runs, logs, or Git.
- All frontend API requests must continue to use `frontend/src/services/api.ts`.
- Do not change Agent skill prompts, registered tools, or output persistence behavior in this provider preset change.

---

### Task 1: Backend Provider Defaults

**Files:**
- Modify: `backend/tests/test_local_llm_config.py`
- Modify: `backend/tests/test_llm_service.py`
- Modify: `backend/services/local_llm_config.py`
- Modify: `backend/services/llm_service.py`

**Interfaces:**
- Produces: `SUPPORTED_PROVIDERS` includes `ollama` and `deepseek`.
- Produces: `LLMConfigurationService.effective_config()` returns default base URLs and endpoint modes for provider presets.
- Produces: `LLMService._create_client()` can create OpenAI SDK clients for `ollama` and `deepseek`.

- [ ] **Step 1: Write failing configuration tests**

Add tests proving:

```python
service.save({"provider": "ollama", "model": "qwen3:8b"})
effective = service.effective_config()
self.assertEqual(effective.base_url, "http://localhost:11434")
self.assertEqual(effective.api_key, "")
self.assertEqual(service.safe_status()["warnings"], [])
```

and:

```python
service.save({"provider": "deepseek", "model": "deepseek-v4-flash", "api_key": "deepseek-secret"})
effective = service.effective_config()
self.assertEqual(effective.base_url, "https://api.deepseek.com")
self.assertEqual(effective.endpoint_mode, "exact")
```

- [ ] **Step 2: Run configuration tests and verify RED**

Run: `cd backend; .\venv\Scripts\python.exe -m unittest tests.test_local_llm_config -v`

Expected: failures for unsupported provider or missing base URL/defaults.

- [ ] **Step 3: Write failing LLM service tests**

Add tests proving `LLMService` builds OpenAI-compatible clients for `ollama` and `deepseek` with normalized base URLs and no leaked real key for Ollama.

- [ ] **Step 4: Run LLM service tests and verify RED**

Run: `cd backend; .\venv\Scripts\python.exe -m unittest tests.test_llm_service -v`

Expected: failures for unsupported providers.

- [ ] **Step 5: Implement minimal backend support**

Update `SUPPORTED_PROVIDERS`, apply provider default base URLs and endpoint modes during effective config resolution, relax key warnings for `ollama`, and route `ollama` / `deepseek` through OpenAI SDK client construction.

- [ ] **Step 6: Verify backend tests GREEN**

Run:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest tests.test_local_llm_config tests.test_llm_service -v
```

Expected: all selected tests pass.

### Task 2: Frontend Provider Presets

**Files:**
- Modify: `frontend/src/views/SettingsView.test.tsx`
- Modify: `frontend/src/components/LLMSettingsPanel.tsx`

**Interfaces:**
- Produces: provider select options for `ollama` and `deepseek`.
- Produces: preset selection updates model, base URL, endpoint mode, and API key helper copy.

- [ ] **Step 1: Write failing UI tests**

Add tests proving selecting `Ollama` and saving sends:

```ts
expect.objectContaining({
  provider: 'ollama',
  model: 'qwen3:8b',
  base_url: 'http://localhost:11434',
  endpoint_mode: 'auto',
})
```

and selecting `DeepSeek` sends:

```ts
expect.objectContaining({
  provider: 'deepseek',
  model: 'deepseek-v4-flash',
  base_url: 'https://api.deepseek.com',
  endpoint_mode: 'exact',
})
```

- [ ] **Step 2: Run UI tests and verify RED**

Run: `cd frontend; npm test -- SettingsView.test.tsx --run`

Expected: failures because provider options or preset behavior do not exist.

- [ ] **Step 3: Implement minimal UI preset behavior**

Add provider options, a small preset map, and provider-change handling in `LLMSettingsPanel.tsx`. Keep all API calls through `settingsApi`.

- [ ] **Step 4: Verify UI tests GREEN**

Run: `cd frontend; npm test -- SettingsView.test.tsx --run`

Expected: selected Settings tests pass.

### Task 3: Commit And Continue Phase 5

**Files:**
- Commit all modified code and tests.

- [ ] **Step 1: Run targeted verification**

Run:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest tests.test_local_llm_config tests.test_llm_service -v
cd ..\frontend
npm test -- SettingsView.test.tsx --run
```

- [ ] **Step 2: Commit**

Run:

```powershell
git add docs/superpowers/specs/2026-07-10-llm-provider-presets-design.md docs/superpowers/plans/2026-07-10-llm-provider-presets.md backend/tests/test_local_llm_config.py backend/tests/test_llm_service.py backend/services/local_llm_config.py backend/services/llm_service.py frontend/src/views/SettingsView.test.tsx frontend/src/components/LLMSettingsPanel.tsx
git commit -m "feat: add ollama and deepseek llm presets"
```

- [ ] **Step 3: Resume Phase 5 manual validation**

Use the updated Settings UI or API to configure a real working provider, then re-run Paper Planner, Course Reviewer, restart recovery checks, final build/tests/compile, key scans, and push only if all Phase 5 completion gates pass.
