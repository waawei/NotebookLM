# Reviva UI and Function Replication Design

## Context

The target project, `mingchen666/Reviva`, has moved beyond a simple NotebookLM-style chat surface. Its current product shape is a local-first learning workbench: document management, conversations, knowledge bases, Wiki, Agents, Skills, tools/MCP, notes, tasks, and generated artifacts are organized around one dense desktop workspace.

Our project already has much of the backend and module foundation: documents, chat, notes, wiki pages, outputs, agents, skills, settings, SQLite persistence, Chroma retrieval, and local LLM configuration. The gap is mostly product composition and interface language. The current UI still reads as a blue SaaS chat shell; Reviva reads as a neutral desktop workbench with small brand accents.

## Product Direction

Replicate Reviva by matching its product structure and interaction model, not by porting its Vue/Electron implementation. Our stack remains React, Tailwind, Vite, FastAPI, SQLite, and Chroma.

The Workbench becomes the primary learning desk:

- Left context panel: conversations, local sources, and knowledge-base context.
- Center workspace: conversation tab strip, message timeline, and compact composer.
- Right panel: Workspace and Preview tabs rather than a citation-only inspector.
- Outputs generated from chat or tools appear as reusable artifacts.
- Agents, Skills, Notes, Wiki, Sources, Outputs, and Settings remain independent modules reachable from the icon rail.

## Visual Language

Reviva's light theme uses warm neutral layers:

- App frame: very light warm gray.
- Panels: slightly darker warm gray.
- Main content paper: white.
- Raised controls: near-white with subtle warm-gray borders.
- Text: dark ink for primary text, muted gray-purple for auxiliary text.
- Blue: brand accent only, not a broad surface color.

Concrete Tailwind direction:

- Replace dominant `bg-blue-600` blocks with `bg-[#eef2ff]`, `bg-[#f5f4f3]`, `bg-white`, or thin accent bars.
- Use `#f8f7f6`, `#f1f0ef`, `#ffffff`, `#f5f4f3`, `#ebeae8` as light surface layers.
- Use `#1a1a2e`, `#5a5a6e`, `#8a8a9e` for text hierarchy.
- Use `#dddcd9` and `#e2e1de` for borders.
- Keep blue only for the active rail indicator, primary Add Source/Send actions, active mode pills, citation number badges, and compact status accents.

Dark mode remains supported, but phase 1 focuses on making light mode match the Reviva-style workbench because that is the screenshot baseline.

## Phase 1 Scope

Phase 1 changes the UI shell and existing Workbench composition without adding new backend behavior.

### Shell

- Re-skin the icon rail so active modules use a pale brand background plus a small left indicator, not a full blue tile.
- Use a warm neutral app background and panel borders.
- Keep the top header compact and desktop-tool-like.
- De-emphasize secondary header buttons; keep Add Source as the main blue action.

### Workbench Left Panel

The current left panel remains powered by `Sidebar`, but Workbench should visually read as a context panel. Phase 1 can keep source management as the only functional content while introducing the Reviva-style panel treatment. Full Conversations/Sources/KB tabs are phase 2.

### Center Workbench

- Add a slim conversation tab strip area above the chat timeline. Phase 1 can show a single static active tab derived from the current conversation state.
- Make the timeline background warm-neutral with white/near-white message paper surfaces.
- Make the empty state compact and workbench-like instead of a large blue hero.
- Make the composer look like a desktop command input: rounded 12px, subtle border, low shadow, toolbar/mode row, compact send button.

### Right Panel

- Rename visual framing from Inspector to a right-side workspace.
- Replace full-width blue active tab blocks with pale blue active pills.
- Keep existing content tabs for Citations, Notes, and Runtime in phase 1, but style them as Workspace sub-tabs.

## Later Phases

Phase 2: Workbench Information Architecture

- Left panel tabs: Conversations, Sources, Knowledge Base.
- Real conversation tab strip with multiple open conversations.
- Context pills for selected sources, wiki pages, and agent.
- Right panel tabs: Workspace and Preview. Current Citations/Notes/Runtime move inside Workspace sections.

Phase 3: Agent and Artifact Workflow

- Agent selector in the composer.
- Slash command menu for bound skills.
- Workspace cards for built-in tools and skills.
- Artifact list that surfaces generated outputs and tasks.

Phase 4: Reviva-like Knowledge Workflows

- Wiki context binding from the Workbench.
- Document preview in the right panel.
- Task progress cards for generated quiz, flashcards, mind maps, charts, research notes, and PPT drafts.
- Recycle bin and richer output lifecycle if needed.

## Testing Strategy

Phase 1 uses UI contract tests rather than pixel snapshots:

- `ModuleNav` active state should use pale accent plus indicator, not full blue tile.
- `WorkbenchShell` should use warm neutral frame/panel classes and expose stable test ids for shell regions.
- `ChatInterface` should expose a conversation tab strip, compact neutral empty state, neutral message surfaces, and compact composer treatment.
- `RightInspector` should use pale active tab styling and neutral citation cards.

Screenshot verification is still required after implementation. Use a local browser/dev server to inspect the wide Workbench layout. If browser automation is unavailable, report that limitation and rely on build/tests plus manual local URL.

## Non-Goals

- Do not port Reviva's Vue/Electron code.
- Do not add Electron-specific filesystem APIs.
- Do not implement MCP, local desktop workdir guards, or deep agent runtime in phase 1.
- Do not rewrite backend storage in this phase.
- Do not remove existing modules that already map to Reviva concepts.
