# Reviva Phase 3 Agent And Artifact Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Reviva-like agent and artifact workflow inside the Workbench: agent selector in the composer, slash-command skill menu, right-panel tool/skill cards, and an artifact list backed by existing outputs/agent runs.

**Architecture:** Build on existing backend `skills`, `agents`, `outputs`, and safe tool registry services. Keep agent execution explicit: selecting a skill creates an inspectable agent run, and generated content appears as a persisted output/artifact. The Workbench UI becomes a launch and monitoring surface; it does not execute arbitrary local commands.

**Tech Stack:** React 18, TypeScript, Zustand, Tailwind CSS, Vitest, React Testing Library, FastAPI existing `skillsApi`, `agentsApi`, `outputApi`.

## Global Constraints

- Do not execute arbitrary shell commands from the frontend or skills.
- Skills may only use registered backend tools.
- Do not expose API keys or provider secrets to the frontend.
- Agent runs must be inspectable through existing `AgentsView` and right-panel workspace cards.
- Artifacts are persisted outputs; no ephemeral-only generated result counts as accepted.
- Keep blue limited to primary actions and active indicators.
- Use TDD for every interaction and API wiring change.

---

## File Structure

- Modify: `frontend/src/store/useStore.ts` for selected agent/skill command state and artifact refresh state.
- Create: `frontend/src/components/AgentSelector.tsx` and `frontend/src/components/AgentSelector.test.tsx`.
- Create: `frontend/src/components/SlashCommandMenu.tsx` and `frontend/src/components/SlashCommandMenu.test.tsx`.
- Create: `frontend/src/components/WorkspaceToolsPanel.tsx` and `frontend/src/components/WorkspaceToolsPanel.test.tsx`.
- Create: `frontend/src/components/ArtifactList.tsx` and `frontend/src/components/ArtifactList.test.tsx`.
- Modify: `frontend/src/components/ChatInterface.tsx` and `frontend/src/components/ChatInterface.test.tsx`.
- Modify: `frontend/src/components/RightInspector.tsx` and `frontend/src/components/RightInspector.test.tsx`.
- Modify: `frontend/src/views/AgentsView.tsx` and `frontend/src/views/OutputsView.tsx` only if navigation affordances are needed.
- Modify: `frontend/src/services/api.ts` only if missing fields are needed for existing backend responses.

## Task 1: Workbench Agent And Command State

**Files:**
- Modify: `frontend/src/store/useStore.ts`
- Modify: `frontend/src/store/useStore.test.ts`

**Interfaces:**
- Produces state: `selectedAgentId: string | null`
- Produces state: `pendingSkillCommand: { skill_id: string; text: string } | null`
- Produces state: `artifactRefreshToken: number`
- Produces actions: `setSelectedAgentId`, `setPendingSkillCommand`, `clearPendingSkillCommand`, `bumpArtifactRefreshToken`

- [ ] **Step 1: Write failing store tests**

Assert:

- Selecting an agent persists through store state updates.
- Setting a pending skill command stores `skill_id` and slash text.
- Clearing command returns `null`.
- `bumpArtifactRefreshToken()` increments monotonically.

- [ ] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- useStore.test.ts --run
```

Expected: FAIL until state/actions exist.

- [ ] **Step 3: Implement store state**

Persist `selectedAgentId` in `localStorage`. Do not persist pending slash commands.

- [ ] **Step 4: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- useStore.test.ts --run
```

Expected: PASS.

## Task 2: Agent Selector In Composer

**Files:**
- Create: `frontend/src/components/AgentSelector.tsx`
- Create: `frontend/src/components/AgentSelector.test.tsx`
- Modify: `frontend/src/components/ChatInterface.tsx`

**Interfaces:**
- Consumes: `skillsApi.list()` or static local agent options if backend does not expose agents separately
- Consumes store: `selectedAgentId`, `setSelectedAgentId`
- Produces button accessible name: `Select agent`
- Produces selected label: default `Default assistant`

- [ ] **Step 1: Write failing tests**

Mock API data and assert:

- Default assistant renders when no agent is selected.
- Opening selector shows available built-in skills/agents.
- Choosing an item updates store.
- Selector uses neutral menu styling and active row uses pale blue, not solid blue.

- [ ] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- AgentSelector.test.tsx --run
```

Expected: FAIL because component does not exist.

- [ ] **Step 3: Implement selector**

Use a compact button in the composer toolbar row. If backend only exposes skills, label this as an agent profile derived from skill metadata.

- [ ] **Step 4: Integrate into ChatInterface**

Place `AgentSelector` near mode options without increasing composer height beyond mobile viewport usability.

- [ ] **Step 5: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- AgentSelector.test.tsx ChatInterface.test.tsx --run
```

Expected: PASS.

## Task 3: Slash Command Skill Menu

**Files:**
- Create: `frontend/src/components/SlashCommandMenu.tsx`
- Create: `frontend/src/components/SlashCommandMenu.test.tsx`
- Modify: `frontend/src/components/ChatInterface.tsx`

**Interfaces:**
- Consumes: `skillsApi.list()`
- Consumes text input value from `ChatInterface`
- Produces command rows with labels like `/paper_planner`
- Produces callback: `onSelect(skill: SkillItem) => void`

- [ ] **Step 1: Write failing tests**

Assert:

- Typing `/` opens the menu.
- Typing `/paper` filters to matching skills.
- Arrow down/up changes highlighted row.
- Enter selects the highlighted skill and inserts command text into composer.
- Escape closes menu without changing input.

- [ ] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- SlashCommandMenu.test.tsx --run
```

Expected: FAIL because component does not exist.

- [ ] **Step 3: Implement keyboard-accessible menu**

Use `role="listbox"` and `role="option"`. Keep dimensions stable so the composer does not jump.

- [ ] **Step 4: Wire to ChatInterface**

When a command is selected:

- Insert `/<skill_id> ` at the start of input.
- Store `pendingSkillCommand`.
- Keep normal chat submission unchanged unless Task 4 explicitly starts a skill run.

- [ ] **Step 5: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- SlashCommandMenu.test.tsx ChatInterface.test.tsx --run
```

Expected: PASS.

## Task 4: Skill Run Submission Path

**Files:**
- Modify: `frontend/src/components/ChatInterface.tsx`
- Modify: `frontend/src/components/ChatInterface.test.tsx`
- Modify: `frontend/src/services/api.ts` only if `agentsApi.createRun()` needs field updates

**Interfaces:**
- Consumes: `pendingSkillCommand`, `selectedDocIds`, input text
- Calls: `agentsApi.createRun({ skill_id, doc_ids, request })`
- Produces: user-visible status message in chat timeline or composer alert
- Produces: artifact refresh via `bumpArtifactRefreshToken()` after run creation

- [ ] **Step 1: Write failing tests**

Mock `agentsApi.createRun()` and assert:

- Submitting `/paper_planner outline chapter 2` calls `agentsApi.createRun()` with `skill_id: 'paper_planner'`, selected docs, and request text without the slash command.
- If no selected docs exist, inline error appears and API is not called.
- Successful creation renders `Agent run started` and links to Agents.
- Failure renders recoverable error text.

- [ ] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- ChatInterface.test.tsx --run
```

Expected: FAIL until slash-command submit path exists.

- [ ] **Step 3: Implement skill submit branch**

In `handleSubmit`, before normal chat stream path:

- If `pendingSkillCommand` exists or input starts with `/<known skill_id>`, use agent run path.
- Do not start a chat stream for skill commands.
- Clear pending command on successful run creation.

- [ ] **Step 4: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- ChatInterface.test.tsx --run
```

Expected: PASS.

## Task 5: Workspace Tool And Skill Cards

**Files:**
- Create: `frontend/src/components/WorkspaceToolsPanel.tsx`
- Create: `frontend/src/components/WorkspaceToolsPanel.test.tsx`
- Modify: `frontend/src/components/RightInspector.tsx`

**Interfaces:**
- Consumes: `skillsApi.list()`
- Consumes selected docs and wiki context from store
- Produces tool cards: `Mind map`, `Quiz`, `Flashcards`, `Research brief`, `Paper outline` as UI launchers where supported by skill manifests
- Produces callback to set pending slash command or create run

- [ ] **Step 1: Write failing tests**

Assert:

- Workspace tab renders a `Tools` section and a `Skills` section.
- Skill cards render name, description, and output kind.
- Clicking a skill card fills composer command or starts run depending on chosen implementation.
- Cards are white/neutral with subtle borders, not blue tiles.

- [ ] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- WorkspaceToolsPanel.test.tsx RightInspector.test.tsx --run
```

Expected: FAIL until panel exists and right panel renders it.

- [ ] **Step 3: Implement panel**

Place it above citations inside the right Workspace tab.

- [ ] **Step 4: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- WorkspaceToolsPanel.test.tsx RightInspector.test.tsx --run
```

Expected: PASS.

## Task 6: Artifact List In Workspace

**Files:**
- Create: `frontend/src/components/ArtifactList.tsx`
- Create: `frontend/src/components/ArtifactList.test.tsx`
- Modify: `frontend/src/components/RightInspector.tsx`
- Modify: `frontend/src/views/OutputsView.tsx` only if output navigation needs query/state support

**Interfaces:**
- Consumes: `outputApi.list()`
- Consumes: `artifactRefreshToken`
- Produces: `data-testid="artifact-list"`
- Produces click callback: set `previewTarget` for the output

- [ ] **Step 1: Write failing tests**

Mock outputs and assert:

- Outputs render as artifact cards grouped by kind.
- Empty state says `No artifacts yet`.
- Refresh token changes trigger reload.
- Clicking an artifact sets Preview target.

- [ ] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- ArtifactList.test.tsx --run
```

Expected: FAIL until component exists.

- [ ] **Step 3: Implement artifact list**

Keep cards compact: title, kind, created date, source count.

- [ ] **Step 4: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- ArtifactList.test.tsx RightInspector.test.tsx --run
```

Expected: PASS.

## Task 7: Phase Verification

- [ ] **Step 1: Run frontend tests**

```powershell
cd frontend
npm.cmd test -- --run
```

Expected: all tests pass.

- [ ] **Step 2: Run backend agent/skill tests**

Use the backend venv if it has test dependencies; otherwise use the known mixed path command:

```powershell
cd backend
$env:PYTHONPATH='D:\develop\python\NotebookLM\backend;D:\develop\python\NotebookLM\backend\venv\Lib\site-packages'
python -m pytest tests\test_skill_service.py tests\test_tool_registry.py tests\test_agent_service.py tests\test_agents_api.py -q
```

Expected: all selected tests pass.

- [ ] **Step 3: Run build**

```powershell
cd frontend
npm.cmd run build
```

Expected: TypeScript and Vite build exit 0.

- [ ] **Step 4: Screenshot verify**

Capture 1440 and 390 viewports.

Expected visual result:

- Composer includes compact agent selector.
- Slash command menu is keyboard usable and not clipped.
- Right Workspace shows Tools, Skills, Artifacts, then evidence sections.
- Artifact click opens Preview.
- No blue card-heavy dashboard look returns.
