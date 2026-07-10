# Reviva Replication Goal Mode Prompts And Acceptance Index

This file contains copy-ready Goal mode wording for each phase. Use one phase at a time. Do not start the next phase until the current phase acceptance checklist is satisfied with fresh verification output.

Current Reviva reference checked: `mingchen666/Reviva` `main` at `a7f2a3ede478566a7f5101d893e088b455bab635` on 2026-07-10.

## Global Goal Rules

- Work in `D:\develop\python\NotebookLM`.
- Preserve the current stack: React, Tailwind, Vite, FastAPI, SQLite, Chroma.
- Do not port Reviva Vue/Electron code.
- Do not add Electron-only APIs.
- Do not expose API keys or local secrets to the frontend.
- Keep local Ollama as the default LLM provider unless the user explicitly changes it.
- Use TDD: failing test first, then implementation, then focused pass.
- Use screenshots for UI acceptance at desktop `1440x900` and mobile `390x844`.
- Keep blue only for primary actions, active indicators/tabs, citation numbers, and small status accents.
- Before claiming completion, run the phase verification commands fresh and report the exact pass/fail evidence.

## Phase 1 Goal Mode Prompt: Neutral Workbench Shell

```text
Goal: Execute Reviva Phase 1 UI Shell polish in D:\develop\python\NotebookLM.

Use docs/superpowers/specs/2026-07-10-reviva-ui-function-replication-design.md and docs/superpowers/plans/2026-07-10-reviva-phase1-ui-shell.md as the source of truth.

Objective:
Re-skin the current Workbench into a low-saturation neutral desktop workbench: warm gray shell, pale active rail/tab states, neutral user messages, white assistant paper, quiet citation cards, compact composer, and right panel titled Workspace.

Required process:
1. Use TDD for each task in the plan.
2. Do not change backend behavior for this phase.
3. Do not port any Reviva code.
4. Keep blue only for Add Source, Send, active tabs/indicators, citation number badges, and compact status accents.
5. After implementation, run focused tests, full frontend tests, frontend build, and Playwright screenshots.

Acceptance:
- Module rail active item is pale blue with a small left indicator, not a solid blue tile.
- Workbench root is warm neutral; left/right panels are warm gray; center is white.
- User messages are shallow gray/blue-gray with dark text, not solid blue.
- Assistant answers use white reading-paper surfaces.
- Citations use white/neutral cards with subtle borders and small numbered badges.
- Right panel heading says Workspace and uses pale active tabs.
- Screenshots at 1440x900 and 390x844 show no text overlap, no blank main canvas, and no large blue blocks.

Verification commands:
cd frontend
npm.cmd test -- --run
npm.cmd run build
npx.cmd playwright screenshot --browser=chromium --viewport-size=1440,900 http://127.0.0.1:3000 ..\phase1-1440.png
npx.cmd playwright screenshot --browser=chromium --viewport-size=390,844 http://127.0.0.1:3000 ..\phase1-390.png
```

## Phase 2 Goal Mode Prompt: Workbench Information Architecture

```text
Goal: Execute Reviva Phase 2 Workbench Information Architecture in D:\develop\python\NotebookLM.

Use docs/superpowers/specs/2026-07-10-reviva-ui-function-replication-design.md and docs/superpowers/plans/2026-07-10-reviva-phase2-workbench-information-architecture.md as the source of truth.

Objective:
Upgrade the Phase 1 visual shell into a functional Reviva-like workbench layout: left panel tabs for Conversations/Sources/Knowledge Base, real conversation tabs in the center, selected context pills, and right panel Workspace/Preview top tabs.

Required process:
1. Use TDD for store state, API wrappers, and each component.
2. Keep backend behavior additive and minimal; reuse existing /api/chat/conversations, /api/documents/search, /api/wiki/pages, notes, outputs, and settings APIs.
3. Do not implement agent runtime or artifact generation in this phase.
4. Preserve Phase 1 neutral styling and blue restrictions.
5. Keep mobile layout usable with no wrapping collisions.

Acceptance:
- Left context panel has three tabs: Conversations, Sources, Knowledge Base.
- Sources tab reuses existing source management and Add Source remains the primary blue action.
- Conversations tab loads persisted conversations, supports opening a conversation tab, and supports delete/reload states.
- Knowledge Base tab lists wiki pages and can toggle wiki context.
- Center tab strip renders real open conversation tabs, close controls, and New conversation.
- Context pill bar shows selected sources and selected wiki pages; pills can be removed.
- Right panel has top-level Workspace and Preview tabs; Preview has an empty state and can show a selected preview target title.
- 1440x900 and 390x844 screenshots show no overlap in tabs, context pills, or composer.

Verification commands:
cd frontend
npm.cmd test -- --run
npm.cmd run build
npx.cmd playwright screenshot --browser=chromium --viewport-size=1440,900 http://127.0.0.1:3000 ..\phase2-1440.png
npx.cmd playwright screenshot --browser=chromium --viewport-size=390,844 http://127.0.0.1:3000 ..\phase2-390.png
```

## Phase 3 Goal Mode Prompt: Agent And Artifact Workflow

```text
Goal: Execute Reviva Phase 3 Agent And Artifact Workflow in D:\develop\python\NotebookLM.

Use docs/superpowers/specs/2026-07-10-reviva-ui-function-replication-design.md and docs/superpowers/plans/2026-07-10-reviva-phase3-agent-artifact-workflow.md as the source of truth.

Objective:
Add Reviva-like agent and artifact workflow to the Workbench: composer agent selector, slash-command skill menu, explicit skill-run submission path, right Workspace tool/skill cards, and artifact list backed by persisted outputs and agent runs.

Required process:
1. Use TDD for store additions, AgentSelector, SlashCommandMenu, skill-run submission, WorkspaceToolsPanel, and ArtifactList.
2. Do not execute arbitrary shell commands.
3. Skills may only call registered backend tools through existing services.
4. Agent runs must be inspectable in AgentsView and must not hide failures.
5. Generated artifacts must be persisted outputs; transient UI-only artifacts do not satisfy the goal.

Acceptance:
- Composer has a compact Agent selector with default assistant state.
- Typing slash commands opens a keyboard-accessible skill menu.
- Submitting a skill command calls agentsApi.createRun with skill ID, selected docs, and request text.
- Missing selected docs blocks skill execution with an inline recoverable error.
- Right Workspace shows Tools, Skills, Artifacts, and evidence sections in neutral cards.
- Artifact cards load from outputApi.list and can open Preview.
- Agent run success/failure is visible without inspecting devtools.
- Screenshots show slash menu and Workspace cards without clipping or broad blue panels.

Verification commands:
cd frontend
npm.cmd test -- --run
npm.cmd run build

cd ..\backend
$env:PYTHONPATH='D:\develop\python\NotebookLM\backend;D:\develop\python\NotebookLM\backend\venv\Lib\site-packages'
python -m pytest tests\test_skill_service.py tests\test_tool_registry.py tests\test_agent_service.py tests\test_agents_api.py -q

cd ..\frontend
npx.cmd playwright screenshot --browser=chromium --viewport-size=1440,900 http://127.0.0.1:3000 ..\phase3-1440.png
npx.cmd playwright screenshot --browser=chromium --viewport-size=390,844 http://127.0.0.1:3000 ..\phase3-390.png
```

## Phase 4 Goal Mode Prompt: Knowledge Workflows

```text
Goal: Execute Reviva Phase 4 Knowledge Workflows in D:\develop\python\NotebookLM.

Use docs/superpowers/specs/2026-07-10-reviva-ui-function-replication-design.md and docs/superpowers/plans/2026-07-10-reviva-phase4-knowledge-workflows.md as the source of truth.

Objective:
Complete the Reviva-like knowledge workflow loop: wiki context binding, document/wiki/note/output preview, generated task progress cards, and durable artifact lifecycle controls.

Required process:
1. Use TDD for backend preview API, frontend PreviewPane, wiki binding, task progress cards, and artifact lifecycle.
2. Keep previews bounded and safe; do not expose local secret paths or raw HTML.
3. Keep artifact lifecycle durable in SQLite or existing output persistence.
4. Do not add Electron-only file preview behavior.
5. Preserve Phase 1-3 layout and visual constraints.

Acceptance:
- Preview API returns typed preview data for document, wiki, note, and output targets.
- Right Preview tab renders empty, loading, error, and loaded states.
- Wiki pages can be selected as context and appear as removable context pills.
- Task progress cards show running, completed, and failed agent/output tasks.
- Completed tasks can open their output artifact in Preview.
- Artifact lifecycle menu supports Preview, Export, and Archive/Restore if lifecycle backend is implemented.
- Archived outputs are hidden from default lists and visible through an explicit archived filter.
- Screenshots show Preview, task cards, and artifact menus without overflow on desktop or mobile.

Verification commands:
cd backend
$env:PYTHONPATH='D:\develop\python\NotebookLM\backend;D:\develop\python\NotebookLM\backend\venv\Lib\site-packages'
python -m pytest tests\test_preview_api.py tests\test_output_export.py tests\test_agent_service.py tests\test_wiki_api.py -q

cd ..\frontend
npm.cmd test -- --run
npm.cmd run build
npx.cmd playwright screenshot --browser=chromium --viewport-size=1440,900 http://127.0.0.1:3000 ..\phase4-1440.png
npx.cmd playwright screenshot --browser=chromium --viewport-size=390,844 http://127.0.0.1:3000 ..\phase4-390.png
```

## Whole-Program Acceptance

The Reviva replication goal is complete only when all of these are true:

- Phase 1 shell is neutral, workbench-like, and screenshot verified.
- Phase 2 information architecture is functional and screenshot verified.
- Phase 3 agent/artifact workflow creates inspectable runs and persisted outputs.
- Phase 4 preview/context/task/lifecycle workflows are implemented and verified.
- Full frontend tests pass.
- Frontend build passes.
- Relevant backend tests pass.
- No Reviva source code has been copied.
- No secrets are exposed to frontend state, responses, logs, or screenshots.
- Local Ollama defaults still work unless explicitly changed by the user.
