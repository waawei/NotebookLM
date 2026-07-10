# Reviva Phase 1 UI Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-skin the current Workbench shell and chat surface toward Reviva's neutral desktop workbench language without changing backend behavior.

**Architecture:** Keep existing React component boundaries. Add class-level UI contract tests, then update Tailwind classes in `ModuleNav`, `WorkbenchShell`, `Sidebar`, `RightInspector`, and `ChatInterface`.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Vitest, React Testing Library, Vite.

## Global Constraints

- Blue is reserved for active indicators, primary actions, citation number badges, and compact status accents.
- Large blue blocks and blue gradient hero surfaces are removed from Workbench phase 1.
- Light theme uses warm neutral layers: `#f8f7f6`, `#f1f0ef`, `#ffffff`, `#f5f4f3`, `#ebeae8`.
- Workbench remains responsive with existing mobile source/inspector controls.
- No backend behavior changes.
- No Vue/Electron code is ported from Reviva.

---

### Task 1: Shell and Rail Visual Contract

**Files:**
- Modify: `frontend/src/components/ModuleNav.test.tsx`
- Modify: `frontend/src/layouts/WorkbenchShell.test.tsx`
- Modify: `frontend/src/components/ModuleNav.tsx`
- Modify: `frontend/src/layouts/WorkbenchShell.tsx`

**Interfaces:**
- Consumes: Existing `AppModule` nav model.
- Produces: Pale active rail buttons, left accent indicator, warm neutral shell surfaces.

- [x] **Step 1: Write failing tests**

Add a `ModuleNav` test asserting the active button uses `bg-blue-50` and contains `data-testid="active-rail-indicator"`, and does not use `bg-blue-600`.

Add a `WorkbenchShell` test asserting the root has `bg-[#f8f7f6]`, the desktop left panel has `bg-[#f1f0ef]`, and the center section has `bg-white`.

- [x] **Step 2: Run tests to verify failure**

Run: `npm.cmd test -- ModuleNav.test.tsx WorkbenchShell.test.tsx --run`

Expected: FAIL because the current rail active state is a full blue tile and shell surfaces are cold gray.

- [x] **Step 3: Implement minimal shell styling**

Update `ModuleNav` active state to pale brand background plus small left indicator.

Update `WorkbenchShell` surfaces to warm neutral frame/panels and white center content.

- [x] **Step 4: Verify focused tests**

Run: `npm.cmd test -- ModuleNav.test.tsx WorkbenchShell.test.tsx --run`

Expected: PASS.

### Task 2: Sidebar Context Panel Visual Contract

**Files:**
- Modify: `frontend/src/components/Sidebar.test.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`

**Interfaces:**
- Consumes: Existing source list and selection state.
- Produces: Reviva-like neutral context panel with pale selected source state.

- [x] **Step 1: Write failing test**

Extend `Sidebar.test.tsx` to assert:

- The expanded sidebar root has `bg-[#f1f0ef]`.
- The Add Source button remains blue as the primary action.
- Selected document card uses `bg-blue-50` and not `bg-blue-600`.
- Empty source icon no longer uses a blue gradient.

- [x] **Step 2: Run test to verify failure**

Run: `npm.cmd test -- Sidebar.test.tsx --run`

Expected: FAIL on current cold-gray panel and blue-gradient empty state.

- [x] **Step 3: Implement sidebar styling**

Use warm neutral panel background, white/near-white cards, subtle border, and pale selected states.

- [x] **Step 4: Verify focused test**

Run: `npm.cmd test -- Sidebar.test.tsx --run`

Expected: PASS.

### Task 3: Workbench Chat Surface Visual Contract

**Files:**
- Modify: `frontend/src/components/ChatInterface.test.tsx`
- Modify: `frontend/src/components/ChatInterface.tsx`

**Interfaces:**
- Consumes: Existing chat messages, citations, composer, and chat mode.
- Produces: Reviva-like tab strip, neutral empty state, compact composer, and lower-blue message styling.

- [x] **Step 1: Write failing test**

Extend `ChatInterface.test.tsx` to assert:

- `data-testid="conversation-tab-strip"` exists.
- Empty state icon is not a blue gradient block.
- The composer input wrapper uses `rounded-xl`, `border`, and not `border-2`.
- The active mode tab uses a pale active background, not full `bg-blue-600`.

- [x] **Step 2: Run test to verify failure**

Run: `npm.cmd test -- ChatInterface.test.tsx --run`

Expected: FAIL because the tab strip does not exist and the composer/empty state still use stronger blue treatment.

- [x] **Step 3: Implement chat visual changes**

Add a slim conversation tab strip above the message timeline.

Replace the empty-state blue gradient icon with a pale neutral/brand icon.

Reduce composer shadow and border weight; keep send button blue only when enabled.

Change active mode tab from solid blue to pale blue background with blue text.

- [x] **Step 4: Verify focused test**

Run: `npm.cmd test -- ChatInterface.test.tsx --run`

Expected: PASS.

### Task 4: Right Workspace Panel Visual Contract

**Files:**
- Modify: `frontend/src/components/RightInspector.tsx`
- Create or modify: `frontend/src/components/RightInspector.test.tsx`

**Interfaces:**
- Consumes: Existing citations, notes, and runtime tabs.
- Produces: Neutral right workspace panel with pale active tabs and quiet citation cards.

- [x] **Step 1: Write failing test**

Add `RightInspector.test.tsx` that renders a citation and asserts:

- The panel heading says `Workspace`.
- The active tab uses `bg-blue-50` and `text-blue-700`, not `bg-blue-600`.
- Citation cards use white background and neutral border.

- [x] **Step 2: Run test to verify failure**

Run: `npm.cmd test -- RightInspector.test.tsx --run`

Expected: FAIL because the heading is still `Inspector` and active tab uses `bg-blue-600`.

- [x] **Step 3: Implement right panel styling**

Rename heading to `Workspace`, update subtitle to match reusable context, and switch active tabs to pale accent styling.

- [x] **Step 4: Verify focused test**

Run: `npm.cmd test -- RightInspector.test.tsx --run`

Expected: PASS.

### Task 5: Full Verification

**Files:**
- No planned code edits.

**Interfaces:**
- Consumes: All phase 1 UI changes.
- Produces: Test, build, and screenshot/manual browser evidence.

- [x] **Step 1: Run full frontend tests**

Run: `npm.cmd test -- --run`

Expected: all frontend tests pass.

- [x] **Step 2: Run frontend build**

Run: `npm.cmd run build`

Expected: TypeScript and Vite build exit 0.

- [x] **Step 3: Run or reuse dev server for visual verification**

Run: `npm.cmd run dev -- --host 127.0.0.1 --port 3000`

Open `http://127.0.0.1:3000/` and inspect wide Workbench layout.

Expected visual result:

- Rail active module is pale with a small indicator.
- Workbench uses warm neutral side panels and white content.
- Blue appears only as action/accent, not large panels.
- Composer is compact, neutral, and desktop-like.
- Right panel reads as Workspace.
