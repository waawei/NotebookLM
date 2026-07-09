# Local LLM Settings and Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Deliver safe, locally persisted user LLM configuration, complete Phase 5 Agent evidence, and a synchronized Reviva-inspired knowledge-workbench interaction model.

**Architecture:** A backend LocalLLMConfigStore persists a write-only local overlay in the Git-ignored runtime directory. A configuration service resolves that overlay over legacy .env settings and creates fresh LLMService instances for each request or Agent run. React receives only safe configuration status through services/api.ts; theme resolution and full-height conversation layout are centralized in the app shell and semantic surface styles.

**Tech Stack:** Python 3, FastAPI, Pydantic, OpenAI Python SDK, SQLite, React 18, TypeScript, Zustand, TailwindCSS, Vitest, Testing Library.

## Global Constraints

- Do not copy Reviva source code, assets, or protected implementation details.
- Do not execute arbitrary shell commands, imports, paths, or user-supplied executable instructions from Skills.
- API keys are write-only and must never enter frontend bundle, browser storage, Zustand persistence, SQLite, logs, API responses, Agent run records, errors, or Git-tracked files.
- Local saved configuration has precedence over compatible .env defaults and must survive backend restart.
- All browser API traffic uses frontend/src/services/api.ts.
- Agents poll run detail every 1500 ms until completed or failed; no simulated status or content.
- Write a failing production-behavior test before each implementation change, run focused verification, and commit each independently working task.

---

## File Structure

- Create: backend/services/local_llm_config.py — atomic Git-ignored runtime-file storage, validation, merge, safe status, and redaction.
- Create: backend/tests/test_local_llm_config.py — storage, restart, precedence, validation, and secret-redaction tests.
- Modify: backend/services/llm_service.py — accept an injected safe effective configuration and remove key-bearing console output.
- Modify: backend/services/agent_service.py — construct an LLM service for each execution and redact every persisted failure boundary.
- Modify: backend/api/settings.py — write-only save/clear endpoints and safe test/status models.
- Create: backend/tests/test_settings_api.py — endpoint response and redaction tests.
- Modify: frontend/package.json, frontend/package-lock.json, frontend/vite.config.ts — add Vitest and DOM test setup.
- Create: frontend/src/test/setup.ts plus focused frontend service, Settings, store, Workbench, and Agents tests.
- Modify: frontend/src/services/api.ts — safe configuration request types and methods.
- Modify: frontend/src/store/useStore.ts, frontend/src/App.tsx, frontend/src/index.css, frontend/src/layouts/WorkbenchShell.tsx, frontend/src/components/ModuleNav.tsx — single theme source and shell propagation.
- Modify: frontend/src/views/SettingsView.tsx and frontend/src/components/SettingsModal.tsx — reusable write-only configuration form.
- Modify: frontend/src/components/ChatInterface.tsx and frontend/src/views/WorkbenchView.tsx — full-height timeline and bottom composer.
- Modify: frontend/src/views/AgentsView.tsx and frontend/src/views/SkillsView.tsx — polling, output links, and safe feedback.

## Task 1: Local configuration service and safe LLM construction

**Files:**

- Create: backend/services/local_llm_config.py
- Create: backend/tests/test_local_llm_config.py
- Modify: backend/services/llm_service.py
- Modify: backend/tests/test_llm_service.py

**Interfaces:**

- Produces: LocalLLMConfigStore(path: str | Path).load() -> dict, save(values: dict) -> dict, clear() -> None.
- Produces: LLMConfigurationService(store, defaults).effective_config() -> EffectiveLLMConfig, safe_status() -> dict, sanitize(message: str, extra_secrets: Iterable[str] = ()) -> str.
- Produces: LLMService(config: EffectiveLLMConfig | None = None).

- [ ] **Step 1: Write failing storage, restart, and redaction tests**

    def test_local_key_overrides_env_and_survives_new_service_instance(self):
        path = Path(self.tempdir.name) / "runtime" / "llm.json"
        first = LLMConfigurationService(LocalLLMConfigStore(path), self.defaults)
        first.save({"provider": "openai_compatible", "model": "local-model", "base_url": "http://localhost:11434", "api_key": "local-secret"})
        second = LLMConfigurationService(LocalLLMConfigStore(path), self.defaults)
        self.assertEqual(second.effective_config().api_key, "local-secret")
        self.assertEqual(second.effective_config().model, "local-model")
        self.assertNotIn("local-secret", str(second.safe_status()))

    def test_sanitize_masks_stored_and_submitted_key(self):
        service = self.make_service(stored_key="stored-secret")
        self.assertEqual(service.sanitize("stored-secret submitted-secret", ["submitted-secret"]), "*** ***")

- [ ] **Step 2: Run test to verify it fails**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_local_llm_config -v

Expected: import failure for services.local_llm_config.

- [ ] **Step 3: Write minimal implementation**

    @dataclass(frozen=True)
    class EffectiveLLMConfig:
        provider: str
        model: str
        base_url: str
        api_key: str
        temperature: float
        max_tokens: int

    class LocalLLMConfigStore:
        def save(self, values: dict) -> dict:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(values), encoding="utf-8")
            os.replace(temporary, self.path)
            return values

Implement provider/base-URL validation, key preservation when save omits api_key, safe status with only booleans and non-secret values, and overlay deletion on clear. Update LLMService to use EffectiveLLMConfig and remove both print(f"LLM ... {e}") paths; raise without console output.

- [ ] **Step 4: Run focused verification**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_local_llm_config tests.test_llm_service -v; .\venv\Scripts\python.exe -m py_compile services/local_llm_config.py services/llm_service.py

Expected: all tests pass and compilation exits 0.

- [ ] **Step 5: Commit**

    git add backend/services/local_llm_config.py backend/services/llm_service.py backend/tests/test_local_llm_config.py backend/tests/test_llm_service.py
    git commit -m "feat: persist local LLM configuration safely"

## Task 2: Safe Settings API and fresh Agent configuration

**Files:**

- Modify: backend/api/settings.py
- Modify: backend/services/agent_service.py
- Modify: backend/tests/test_agent_service.py
- Create: backend/tests/test_settings_api.py

**Interfaces:**

- Consumes: LLMConfigurationService.safe_status/save/clear/sanitize.
- Produces: PUT /api/settings/llm accepting provider, model, base_url, and optional write-only api_key.
- Produces: DELETE /api/settings/llm, GET /api/settings/status, POST /api/settings/test-llm, returning safe models.
- Produces: AgentService(..., llm_factory: Callable[[], LLMService] | None = None).

- [ ] **Step 1: Write failing API and Agent tests**

    def test_save_returns_safe_status_without_api_key(self):
        response = asyncio.run(settings.save_llm_configuration(
            settings.LLMConfigUpdate(provider="openai", model="gpt-test", base_url="", api_key="do-not-return")
        ))
        self.assertTrue(response.api_key_configured)
        self.assertNotIn("api_key", response.model_dump())
        self.assertNotIn("do-not-return", str(response))

    def test_each_agent_execution_uses_a_fresh_llm_service(self):
        factory = FakeLLMFactory(["first", "second"])
        service = AgentService(metadata_store=self.store, skill_service=self.skills, tool_registry=self.tools, llm_factory=factory)
        asyncio.run(service.execute_run(service.create_run("paper_planner", {"doc_ids": []})["run_id"]))
        asyncio.run(service.execute_run(service.create_run("paper_planner", {"doc_ids": []})["run_id"]))
        self.assertEqual(factory.calls, 2)

- [ ] **Step 2: Run test to verify it fails**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_settings_api tests.test_agent_service -v

Expected: missing save_llm_configuration and unsupported llm_factory argument.

- [ ] **Step 3: Write minimal implementation**

    class LLMConfigUpdate(BaseModel):
        provider: str
        model: str
        base_url: str = ""
        api_key: str | None = Field(default=None, repr=False)

    @router.put("/llm", response_model=SettingsStatus)
    async def save_llm_configuration(update: LLMConfigUpdate):
        configuration_service.save(update.model_dump(exclude_none=True))
        return SettingsStatus(**configuration_service.safe_status())

Make test_llm_connection build a fresh LLMService from effective_config. Return a fixed sanitized provider-failure message. In AgentService, retain llm_factory and call it inside execute_run. Sanitize errors before append_agent_step and update_agent_run_status. Keep injected factories usable by existing unit tests.

- [ ] **Step 4: Run focused verification**

Run: cd backend; $env:DEBUG='false'; .\venv\Scripts\python.exe -m unittest tests.test_settings_api tests.test_agent_service tests.test_agents_api tests.test_agent_store -v

Expected: all listed tests pass with no fixture key serialized.

- [ ] **Step 5: Commit**

    git add backend/api/settings.py backend/services/agent_service.py backend/tests/test_settings_api.py backend/tests/test_agent_service.py
    git commit -m "feat: add safe local LLM settings API"

## Task 3: Frontend behavior-test foundation and safe API client

**Files:**

- Modify: frontend/package.json, frontend/package-lock.json, frontend/vite.config.ts
- Create: frontend/src/test/setup.ts
- Create: frontend/src/services/api.test.ts
- Modify: frontend/src/services/api.ts

**Interfaces:**

- Produces: npm run test -- --run using jsdom.
- Produces: SettingsConfigUpdate with optional api_key used only in the request body; settingsApi.save, clear, testLlm, getStatus.

- [ ] **Step 1: Write failing API-client test**

    it("sends a key only in the save request and never receives it in status", async () => {
      global.fetch = vi.fn().mockResolvedValue(jsonResponse(safeStatus))
      await settingsApi.save({ provider: "openai", model: "gpt-test", base_url: "", api_key: "browser-only-secret" })
      expect(fetch).toHaveBeenCalledWith("/api/settings/llm", expect.objectContaining({ method: "PUT" }))
      expect(JSON.stringify(safeStatus)).not.toContain("browser-only-secret")
    })

- [ ] **Step 2: Run test to verify it fails**

Run: cd frontend; npm run test -- --run src/services/api.test.ts

Expected: Missing script: "test".

- [ ] **Step 3: Write minimal implementation**

    // vite.config.ts
    test: { environment: "jsdom", setupFiles: "./src/test/setup.ts", globals: true }

    export const settingsApi = {
      getStatus: async (): Promise<SettingsStatus> => (await api.get("/settings/status")).data,
      save: async (data: SettingsConfigUpdate): Promise<SettingsStatus> => (await api.put("/settings/llm", data)).data,
      clear: async (): Promise<SettingsStatus> => (await api.delete("/settings/llm")).data,
      testLlm: async (): Promise<SettingsTestResult> => (await api.post("/settings/test-llm")).data,
    }

Add vitest, jsdom, @testing-library/react, and @testing-library/jest-dom as development dependencies. The setup imports @testing-library/jest-dom/vitest. Add no browser configuration persistence.

- [ ] **Step 4: Run focused verification**

Run: cd frontend; npm run test -- --run src/services/api.test.ts; npm run build

Expected: test passes and build exits 0.

- [ ] **Step 5: Commit**

    git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts frontend/src/test/setup.ts frontend/src/services/api.ts frontend/src/services/api.test.ts
    git commit -m "test: cover safe LLM settings API client"

## Task 4: Write-only Settings UI

**Files:**

- Modify: frontend/src/views/SettingsView.tsx
- Modify: frontend/src/components/SettingsModal.tsx
- Create: frontend/src/views/SettingsView.test.tsx

**Interfaces:**

- Consumes: settingsApi.getStatus/save/clear/testLlm.
- Produces: a password API key field that starts blank and resets after save/test; status cards receive only SettingsStatus.

- [ ] **Step 1: Write failing Settings view test**

    it("submits but never renders a configured API key", async () => {
      render(<SettingsView />)
      await userEvent.type(screen.getByLabelText("API key"), "write-only-key")
      await userEvent.click(screen.getByRole("button", { name: "Save configuration" }))
      await waitFor(() => expect(settingsApi.save).toHaveBeenCalledWith(expect.objectContaining({ api_key: "write-only-key" })))
      expect(screen.queryByDisplayValue("write-only-key")).not.toBeInTheDocument()
      expect(screen.queryByText("write-only-key")).not.toBeInTheDocument()
    })

- [ ] **Step 2: Run test to verify it fails**

Run: cd frontend; npm run test -- --run src/views/SettingsView.test.tsx

Expected: unable to find API key and Save configuration.

- [ ] **Step 3: Write minimal implementation**

    <input aria-label="API key" type="password" autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)} />
    <button onClick={saveConfiguration} disabled={isSaving}>Save configuration</button>
    <button onClick={clearConfiguration} disabled={isClearing}>Clear local configuration</button>

Keep provider/model/base URL/key in component-local state; use only services/api.ts; call setApiKey("") in finally after save and test; use fixed safe failure copy. Share the configuration content between module and modal to avoid divergent secret behavior. Remove console.error paths that can record provider responses.

- [ ] **Step 4: Run focused verification**

Run: cd frontend; npm run test -- --run src/services/api.test.ts src/views/SettingsView.test.tsx; npm run build

Expected: all tests pass and build exits 0.

- [ ] **Step 5: Commit**

    git add frontend/src/views/SettingsView.tsx frontend/src/components/SettingsModal.tsx frontend/src/views/SettingsView.test.tsx
    git commit -m "feat: add write-only local LLM settings"

## Task 5: Single theme source and shell synchronization

**Files:**

- Modify: frontend/src/store/useStore.ts, frontend/src/App.tsx, frontend/src/index.css, frontend/src/layouts/WorkbenchShell.tsx, frontend/src/components/ModuleNav.tsx
- Create: frontend/src/store/useStore.test.ts

**Interfaces:**

- Produces: theme: "system" | "light" | "dark", setTheme(theme), and document-root synchronization.
- Consumes: matchMedia("(prefers-color-scheme: dark)") only for system preference.

- [ ] **Step 1: Write failing theme test**

    it("changes the document root when set to dark and light", () => {
      useStore.getState().setTheme("dark")
      expect(document.documentElement.classList.contains("dark")).toBe(true)
      useStore.getState().setTheme("light")
      expect(document.documentElement.classList.contains("dark")).toBe(false)
    })

- [ ] **Step 2: Run test to verify it fails**

Run: cd frontend; npm run test -- --run src/store/useStore.test.ts

Expected: missing setTheme.

- [ ] **Step 3: Write minimal implementation**

    export type ThemePreference = "system" | "light" | "dark"
    setTheme: (theme) => set({ theme })

Resolve the preference in App, add/remove the root dark class, and listen for system preference changes only while the preference is system. Replace always-dark ModuleNav classes with paired semantic light/dark surface classes. Add short color/background/border transitions and a prefers-reduced-motion override in index.css. Do not persist any LLM configuration, source data, or messages.

- [ ] **Step 4: Run focused verification**

Run: cd frontend; npm run test -- --run src/store/useStore.test.ts; npm run lint; npm run build

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

    git add frontend/src/store/useStore.ts frontend/src/App.tsx frontend/src/index.css frontend/src/layouts/WorkbenchShell.tsx frontend/src/components/ModuleNav.tsx frontend/src/store/useStore.test.ts
    git commit -m "feat: synchronize workbench theme surfaces"

## Task 6: Continuous Workbench conversation layout

**Files:**

- Modify: frontend/src/components/ChatInterface.tsx, frontend/src/views/WorkbenchView.tsx, frontend/src/layouts/WorkbenchShell.tsx
- Create: frontend/src/components/ChatInterface.test.tsx

**Interfaces:**

- Consumes: selected documents, streaming chatApi.createStreamRequest, messages, citations, and note creation.
- Produces: data-testid="message-timeline" scroll region and data-testid="chat-composer" bottom composer.

- [ ] **Step 1: Write failing layout tests**

    it("renders messages in a timeline and keeps the composer in the workspace", () => {
      render(<ChatInterface />)
      expect(screen.getByTestId("message-timeline")).toHaveClass("flex-1")
      expect(screen.getByTestId("chat-composer")).toHaveClass("sticky")
    })

    it("keeps source selection available", () => {
      render(<ChatInterface />)
      expect(screen.getByText(/selected sources/i)).toBeInTheDocument()
    })

- [ ] **Step 2: Run test to verify it fails**

Run: cd frontend; npm run test -- --run src/components/ChatInterface.test.tsx

Expected: timeline and composer test IDs do not exist.

- [ ] **Step 3: Write minimal implementation**

    <section className="flex min-h-0 flex-1 flex-col" aria-label="Conversation workspace">
      <div data-testid="message-timeline" className="min-h-0 flex-1 overflow-y-auto px-4 py-6">...</div>
      <form data-testid="chat-composer" className="sticky bottom-0 border-t bg-inherit p-4">...</form>
    </section>

Remove only the centered isolated conversation-card wrapper. Preserve stream parsing, selected-doc guard, suggested questions, citations, expansion, and note capture. Use responsive panel rules so inspector and source controls remain accessible on small screens.

- [ ] **Step 4: Run focused verification**

Run: cd frontend; npm run test -- --run src/components/ChatInterface.test.tsx; npm run build

Expected: tests pass and build exits 0.

- [ ] **Step 5: Commit**

    git add frontend/src/components/ChatInterface.tsx frontend/src/views/WorkbenchView.tsx frontend/src/layouts/WorkbenchShell.tsx frontend/src/components/ChatInterface.test.tsx
    git commit -m "feat: make workbench chat a continuous workspace"

## Task 7: Inspectable Skills and Agent run feedback

**Files:**

- Modify: frontend/src/views/AgentsView.tsx, frontend/src/views/SkillsView.tsx, frontend/src/services/api.ts
- Create: frontend/src/views/AgentsView.test.tsx

**Interfaces:**

- Consumes: agentsApi.listRuns/getRun/createRun, skillsApi.list, outputApi.get.
- Produces: polling at 1500 ms for active runs only, terminal cancellation, output link, and safe error rendering.

- [ ] **Step 1: Write failing polling/output-link test**

    it("polls running work every 1500ms and stops after completion", async () => {
      vi.useFakeTimers()
      mockedAgentsApi.listRuns.mockResolvedValue({ runs: [runningRun], total: 1 })
      mockedAgentsApi.getRun.mockResolvedValueOnce(runningRun).mockResolvedValueOnce(completedRun)
      render(<AgentsView />)
      await vi.advanceTimersByTimeAsync(3000)
      expect(mockedAgentsApi.getRun).toHaveBeenCalledTimes(2)
      expect(screen.getByRole("link", { name: /open output/i })).toHaveAttribute("href", expect.stringContaining(completedRun.output_id))
    })

- [ ] **Step 2: Run test to verify it fails**

Run: cd frontend; npm run test -- --run src/views/AgentsView.test.tsx

Expected: output is not a link or active detail polling assertion fails.

- [ ] **Step 3: Write minimal implementation**

    useEffect(() => {
      const activeIds = runs.filter((run) => run.status === "running").map((run) => run.run_id)
      if (!activeIds.length) return
      const timer = window.setInterval(() => void refreshActiveRuns(activeIds), 1500)
      return () => window.clearInterval(timer)
    }, [runs])

Fetch detail for every active ID and merge by run_id; stop when no run is active; expose retryable load failure. Render an output route/link from output_id only. Skills displays manifest fields, disables its button while creating, emits fixed safe failure copy, and refreshes/navigates to Agents after creation.

- [ ] **Step 4: Run focused verification**

Run: cd frontend; npm run test -- --run src/views/AgentsView.test.tsx; npm run lint; npm run build

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

    git add frontend/src/views/AgentsView.tsx frontend/src/views/SkillsView.tsx frontend/src/services/api.ts frontend/src/views/AgentsView.test.tsx
    git commit -m "feat: improve inspectable agent run feedback"

## Task 8: Full verification, real local acceptance, and push

**Files:**

- Modify only after a demonstrated defect; first add a failing regression test and then commit the correction.

**Interfaces:**

- Consumes: completed settings and Agent APIs plus a user-entered valid local credential.
- Produces: current evidence for real paper_plan/review_cards outputs, restart persistence, clean pushed branch.

- [ ] **Step 1: Run mandatory automated verification**

Run:

    cd frontend
    npm run build
    npm run test -- --run
    cd ..\backend
    $env:DEBUG='false'
    .\venv\Scripts\python.exe -m unittest discover -s tests -v
    $files = Get-ChildItem -Recurse -Include *.py | Where-Object { $_.FullName -notmatch '\\venv\\' } | ForEach-Object { $_.FullName }
    .\venv\Scripts\python.exe -m py_compile @files

Expected: every command exits 0.

- [ ] **Step 2: Perform safe configuration acceptance**

Start backend and frontend locally. Save a valid credential in Settings; verify safe status only reports api_key_configured/provider/model/Base URL state/warnings. Restart backend and verify status persists. Search browser storage, responses, SQLite, Agent records, logs, Git status, and ignored runtime content for the test key: it appears only in the ignored runtime file. Clear local configuration and confirm fallback to .env/default safe status.

- [ ] **Step 3: Perform real Agent acceptance**

Upload/select a small local source. With valid local configuration, run Paper Planner, verify completed state, persisted paper_plan, steps, output link, and restart recovery. Repeat Course Reviewer and verify review_cards. Save an invalid key/endpoint and verify the connection/run error is understandable but never shows the key.

- [ ] **Step 4: Perform visual acceptance**

Verify light/dark/system synchronizes module rail, sidebar, workspace, panels, Settings form, and modal. Verify desktop/narrow Workbench continuous stream, bottom composer, source selection, citations/inspector, streaming state, Skills loading/failure, and Agent 1500 ms polling.

- [ ] **Step 5: Commit demonstrated regression fixes, then push clean history**

    git status --short
    git log --oneline origin/main..HEAD
    git push origin main
    git status --short --branch

Expected: no uncommitted changes, push succeeds, and branch is no longer ahead of origin/main.

## Plan Self-Review

- Spec coverage: Tasks 1-2 deliver local persistence, safe API, precedence, redaction, and fresh Agents; Tasks 3-4 deliver write-only browser configuration; Tasks 5-7 deliver theme, continuous Workbench, and Agents/Skills feedback; Task 8 covers real generation, restart, build, tests, compile, clean status, and push.
- Placeholder scan: Every production task names files, interfaces, failing tests, commands, implementation actions, and commit boundaries.
- Type consistency: backend uses EffectiveLLMConfig, LLMConfigUpdate, LLMConfigurationService, and llm_factory consistently; frontend uses SettingsConfigUpdate, SettingsStatus, and settingsApi consistently.

