# Reviva Phase 2 Workbench Information Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the phase 1 neutral Workbench shell into a Reviva-like working desk with left-panel Conversations/Sources/Knowledge Base tabs, real conversation tabs in the center, context pills, and a right panel split into Workspace and Preview.

**Architecture:** Keep the current React/FastAPI stack. Reuse existing backend conversation, document, spaces, wiki, note, output, skills, and agents APIs where possible; add only small frontend state and missing API wrappers. The phase is primarily information architecture and interaction wiring, not new retrieval or agent behavior.

**Tech Stack:** React 18, TypeScript, Zustand, Tailwind CSS, Vitest, React Testing Library, Playwright CLI screenshots, FastAPI existing endpoints.

## Global Constraints

- Do not port Reviva Vue/Electron code.
- Do not add Electron or local filesystem APIs.
- Blue remains limited to primary actions, active pills, indicators, and compact status accents.
- Preserve phase 1 warm neutral surfaces: `#f8f7f6`, `#f1f0ef`, `#ffffff`, `#f5f4f3`, `#ebeae8`.
- All frontend API wrappers stay in `frontend/src/services/api.ts`.
- Keep backend behavior additive; do not remove existing routes.
- Use TDD: write failing tests before implementation for every behavior change.
- Every task ends with focused tests passing before moving on.

---

## File Structure

- Modify: `frontend/src/services/api.ts` for `chatApi.listConversations()` and typed conversation summaries if missing.
- Modify: `frontend/src/store/useStore.ts` for workbench left tab, open conversation tabs, active preview target, selected wiki context, and context pills.
- Create: `frontend/src/components/WorkbenchContextPanel.tsx` and `frontend/src/components/WorkbenchContextPanel.test.tsx`.
- Create: `frontend/src/components/ConversationTabStrip.tsx` and `frontend/src/components/ConversationTabStrip.test.tsx`.
- Create: `frontend/src/components/ContextPillBar.tsx` and `frontend/src/components/ContextPillBar.test.tsx`.
- Modify: `frontend/src/components/ChatInterface.tsx` and `frontend/src/components/ChatInterface.test.tsx` to use the real tab strip and context pills.
- Modify: `frontend/src/components/RightInspector.tsx` and `frontend/src/components/RightInspector.test.tsx` to expose `Workspace` and `Preview` top tabs.
- Modify: `frontend/src/App.tsx` to pass preview/context state between shell panels.

## Task 1: Workbench State Model

**Files:**
- Modify: `frontend/src/store/useStore.ts`
- Create or modify: `frontend/src/store/useStore.test.ts`

**Interfaces:**
- Produces type: `WorkbenchLeftTab = 'conversations' | 'sources' | 'knowledge_base'`
- Produces type: `OpenConversationTab = { conversation_id: string | null; title: string; isDirty?: boolean }`
- Produces type: `PreviewTarget = { type: 'document' | 'wiki' | 'note' | 'output'; id: string; title: string } | null`
- Produces state: `workbenchLeftTab`, `openConversationTabs`, `activeConversationTabId`, `previewTarget`, `selectedWikiPageIds`
- Produces actions: `setWorkbenchLeftTab`, `openConversationTab`, `closeConversationTab`, `setActiveConversationTab`, `setPreviewTarget`, `toggleWikiContext`

- [x] **Step 1: Write failing store tests**

Assert:

- Default `workbenchLeftTab` is `conversations`.
- `openConversationTab({ conversation_id: 'conv-1', title: 'Paper notes' })` adds the tab and sets it active.
- Opening the same conversation twice does not duplicate it.
- Closing the active tab selects the nearest remaining tab or falls back to a new chat tab.
- `setPreviewTarget()` stores and clears preview targets.
- `toggleWikiContext()` adds/removes wiki page IDs without duplicates.

- [x] **Step 2: Run the failing test**

Run:

```powershell
cd frontend
npm.cmd test -- useStore.test.ts --run
```

Expected: FAIL because these fields/actions do not exist.

- [x] **Step 3: Implement store state and actions**

Keep persistence minimal:

- Persist `openConversationTabs`, `activeConversationTabId`, and `selectedWikiPageIds` to `localStorage`.
- Do not persist `previewTarget`; preview is session UI state.
- Keep current `conversationId`/`messages` behavior compatible with existing chat tests.

- [x] **Step 4: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- useStore.test.ts --run
```

Expected: PASS.

## Task 2: Left Context Panel Tabs

**Files:**
- Create: `frontend/src/components/WorkbenchContextPanel.tsx`
- Create: `frontend/src/components/WorkbenchContextPanel.test.tsx`
- Modify: `frontend/src/App.tsx`
- Keep: `frontend/src/components/Sidebar.tsx` as the Sources tab content

**Interfaces:**
- Consumes store `workbenchLeftTab`, `setWorkbenchLeftTab`
- Consumes existing `Sidebar` props: `isCollapsed`, `onToggle`, `onUploadClick`
- Produces `data-testid="workbench-context-panel"`
- Produces tab buttons with accessible names: `Conversations`, `Sources`, `Knowledge Base`

- [x] **Step 1: Write failing component tests**

Assert:

- The panel renders all three tabs.
- The active tab uses `bg-blue-50 text-blue-700` and not `bg-blue-600`.
- Clicking `Sources` renders existing source content including `Add source`.
- Clicking `Conversations` renders a conversation list placeholder/loaded list region with `data-testid="conversation-list"`.
- Clicking `Knowledge Base` renders a wiki context list region with `data-testid="kb-context-list"`.

- [x] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- WorkbenchContextPanel.test.tsx --run
```

Expected: FAIL because the component does not exist.

- [x] **Step 3: Implement the tabbed panel**

Implementation notes:

- Use warm neutral panel classes from phase 1.
- Reuse `Sidebar` only inside the `Sources` tab.
- For `Conversations`, call `chatApi.listConversations()` if Task 3 has added it; otherwise render empty state and wire later.
- For `Knowledge Base`, call `wikiApi.list()` and let users toggle wiki context through store.

- [x] **Step 4: Replace `App.tsx` leftPanel**

Replace direct `<Sidebar />` usage with `<WorkbenchContextPanel />`.

- [x] **Step 5: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- WorkbenchContextPanel.test.tsx --run
```

Expected: PASS.

## Task 3: Conversation List API Wrapper And Loading UI

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/components/WorkbenchContextPanel.tsx`
- Modify: `frontend/src/components/WorkbenchContextPanel.test.tsx`

**Interfaces:**
- Produces type: `ConversationSummary = { conversation_id: string; title: string; updated_at: string; message_count: number; latest_message?: string | null }`
- Produces API wrapper: `chatApi.listConversations(): Promise<{ conversations: ConversationSummary[] }>`

- [x] **Step 1: Write failing API/component tests**

Mock `chatApi.listConversations()` and assert:

- Conversation titles render in the Conversations tab.
- Clicking a conversation calls `openConversationTab()` and `setConversationId()`.
- Delete action calls existing `chatApi.deleteConversation()` and removes the row after success.

- [x] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- WorkbenchContextPanel.test.tsx api.test.ts --run
```

Expected: FAIL until API wrapper and UI wiring exist.

- [x] **Step 3: Add API wrapper**

In `frontend/src/services/api.ts`, add:

```ts
listConversations: async (): Promise<{ conversations: ConversationSummary[] }> => {
  const response = await api.get('/chat/conversations')
  return response.data
}
```

- [x] **Step 4: Wire list loading states**

Render:

- Loading row while fetching.
- Empty state when no conversations exist.
- Error state with retry button on failure.

- [x] **Step 5: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- WorkbenchContextPanel.test.tsx api.test.ts --run
```

Expected: PASS.

## Task 4: Real Conversation Tab Strip

**Files:**
- Create: `frontend/src/components/ConversationTabStrip.tsx`
- Create: `frontend/src/components/ConversationTabStrip.test.tsx`
- Modify: `frontend/src/components/ChatInterface.tsx`
- Modify: `frontend/src/components/ChatInterface.test.tsx`

**Interfaces:**
- Consumes: `openConversationTabs`, `activeConversationTabId`, `setActiveConversationTab`, `closeConversationTab`, `clearChat`
- Produces: `data-testid="conversation-tab-strip"` from the new component
- Produces action button: accessible name `New conversation`

- [x] **Step 1: Write failing tests**

Assert:

- Open tabs render with titles.
- Active tab uses pale blue active state and not solid blue.
- Close button removes a tab.
- `New conversation` clears chat and opens/selects a local new-chat tab.
- On mobile width, tabs remain horizontally scrollable and do not wrap into overlapping rows.

- [x] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- ConversationTabStrip.test.tsx ChatInterface.test.tsx --run
```

Expected: FAIL because only static Phase 1 tab strip exists.

- [x] **Step 3: Implement `ConversationTabStrip`**

Use fixed-height `h-11`, `overflow-x-auto`, and stable tab dimensions to avoid layout shifts.

- [x] **Step 4: Replace static strip in `ChatInterface`**

Remove the hard-coded `Conversation/Sources` buttons and render `<ConversationTabStrip />`.

- [x] **Step 5: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- ConversationTabStrip.test.tsx ChatInterface.test.tsx --run
```

Expected: PASS.

## Task 5: Context Pill Bar

**Files:**
- Create: `frontend/src/components/ContextPillBar.tsx`
- Create: `frontend/src/components/ContextPillBar.test.tsx`
- Modify: `frontend/src/components/ChatInterface.tsx`

**Interfaces:**
- Consumes: selected documents from `documents` + `selectedDocIds`
- Consumes: selected wiki pages from `selectedWikiPageIds`
- Produces: removable pills with accessible names `Remove source <name>` and `Remove wiki <name>`

- [x] **Step 1: Write failing tests**

Assert:

- Selected document names appear as neutral pills.
- Wiki context appears as neutral pills.
- Removing a source calls `toggleDocumentSelection(doc_id)`.
- Removing a wiki page calls `toggleWikiContext(page_id)`.
- Empty state renders `No context selected`.

- [x] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- ContextPillBar.test.tsx --run
```

Expected: FAIL because component does not exist.

- [x] **Step 3: Implement pill bar**

Render above composer mode row. Keep height bounded and wrap gracefully on mobile.

- [x] **Step 4: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- ContextPillBar.test.tsx ChatInterface.test.tsx --run
```

Expected: PASS.

## Task 6: Right Panel Workspace / Preview Split

**Files:**
- Modify: `frontend/src/components/RightInspector.tsx`
- Modify: `frontend/src/components/RightInspector.test.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `previewTarget`, `setPreviewTarget`
- Produces top tabs: `Workspace`, `Preview`
- Produces `data-testid="workspace-tab-panel"` and `data-testid="preview-tab-panel"`

- [x] **Step 1: Write failing tests**

Assert:

- The right panel has top-level `Workspace` and `Preview` tabs.
- `Workspace` tab contains the current Citations/Notes/Runtime sections.
- Setting a document preview target switches to Preview and renders the target title.
- Empty Preview state says `Select an item to preview`.
- Active top tab uses pale blue, not solid blue.

- [x] **Step 2: Run failing tests**

Run:

```powershell
cd frontend
npm.cmd test -- RightInspector.test.tsx --run
```

Expected: FAIL because the top-level split does not exist.

- [x] **Step 3: Implement split**

Keep existing citations/notes/runtime as inner Workspace sections. Preview can be text/metadata preview in Phase 2; full document preview belongs to Phase 4.

- [x] **Step 4: Verify focused tests**

Run:

```powershell
cd frontend
npm.cmd test -- RightInspector.test.tsx --run
```

Expected: PASS.

## Task 7: Full Phase Verification

**Files:**
- No planned code edits.

- [x] **Step 1: Run frontend tests**

Run:

```powershell
cd frontend
npm.cmd test -- --run
```

Expected: all tests pass.

- [x] **Step 2: Run build**

Run:

```powershell
cd frontend
npm.cmd run build
```

Expected: TypeScript and Vite build exit 0.

- [x] **Step 3: Screenshot verify**

Use existing dev server or run:

```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 3000
```

Capture:

```powershell
cd frontend
npx.cmd playwright screenshot --browser=chromium --viewport-size=1440,900 http://127.0.0.1:3000 ..\phase2-1440.png
npx.cmd playwright screenshot --browser=chromium --viewport-size=390,844 http://127.0.0.1:3000 ..\phase2-390.png
```

Expected visual result:

- Left panel has Conversations/Sources/Knowledge Base tabs.
- Center has real conversation tabs and context pills.
- Right panel has Workspace/Preview top tabs.
- No large solid-blue panels appear except primary action buttons.
- Mobile viewport has no text overlap in tabs, pill bar, or composer.
