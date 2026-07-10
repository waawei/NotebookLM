# Workbench Neutral UI Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the Workbench chat visual treatment so user messages, assistant answers, and citation cards use low-saturation neutral workbench styling.

**Architecture:** Keep the existing `ChatInterface` component and Tailwind utility approach. Add class-level contract tests for message and citation surfaces, then update only the role-specific message and citation class names needed to satisfy the contract.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Vitest, React Testing Library, Vite.

## Global Constraints

- User messages use light gray/blue-gray surfaces with dark text, not saturated blue blocks.
- Blue remains reserved for primary actions, current tabs, compact badges, and status/action accents.
- Assistant answers use white reading-paper surfaces with readable neutral prose.
- Citation cards use subtle neutral borders/backgrounds and small numbered badges, not broad blue fills.
- No backend changes.
- No Workbench shell layout restructure.

---

### Task 1: Add Message Surface Visual Contract Test

**Files:**
- Modify: `frontend/src/components/ChatInterface.test.tsx`
- Test: `frontend/src/components/ChatInterface.test.tsx`

**Interfaces:**
- Consumes: `useStore.setState({ messages })` from `frontend/src/store/useStore.ts`
- Produces: A failing test named `uses neutral workbench surfaces for messages and citations`

- [ ] **Step 1: Write the failing test**

Add this test inside `describe('ChatInterface workspace layout', () => { ... })`:

```tsx
  it('uses neutral workbench surfaces for messages and citations', () => {
    useStore.setState({
      messages: [
        { role: 'user', content: 'Compare these two sections.' },
        {
          role: 'assistant',
          content: 'The second section narrows the claim.',
          citations: [
            {
              number: 1,
              doc_id: 'doc-1',
              doc_name: 'Research Brief.pdf',
              page: 4,
              chunk_id: 2,
              content: 'The cited passage supports the narrowed claim.',
              relevance_score: 0.92,
            },
          ],
        },
      ],
    })

    render(<ChatInterface />)

    const userBubble = screen.getByText('Compare these two sections.').closest('[data-message-role="user"]')
    expect(userBubble).toHaveClass('bg-slate-100')
    expect(userBubble).toHaveClass('text-slate-900')
    expect(userBubble).not.toHaveClass('bg-blue-600')
    expect(userBubble).not.toHaveClass('text-white')

    const assistantPaper = screen.getByText('The second section narrows the claim.').closest('[data-message-role="assistant"]')
    expect(assistantPaper).toHaveClass('bg-white')
    expect(assistantPaper).toHaveClass('border-slate-200')

    const citationCard = screen.getByText('Research Brief.pdf').closest('[data-testid="citation-card"]')
    expect(citationCard).toHaveClass('bg-white')
    expect(citationCard).toHaveClass('border-slate-200')
    expect(citationCard).not.toHaveClass('bg-blue-50')

    expect(screen.getByText('1')).toHaveClass('bg-blue-600')
  })
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- ChatInterface.test.tsx --run`

Expected: FAIL because message wrappers do not yet expose `data-message-role`/`data-testid` and the current user/citation classes are still saturated blue.

- [ ] **Step 3: Commit**

Do not commit unless the user explicitly asks for a commit.

### Task 2: Apply Neutral Message and Citation Styling

**Files:**
- Modify: `frontend/src/components/ChatInterface.tsx`
- Test: `frontend/src/components/ChatInterface.test.tsx`

**Interfaces:**
- Consumes: The failing test from Task 1.
- Produces: Message wrappers with `data-message-role`, citation cards with `data-testid="citation-card"`, and neutral Tailwind class treatment.

- [ ] **Step 1: Add message role test hooks and neutral role classes**

Change the mapped message card wrapper to include `data-message-role={message.role}` and use these role-specific class groups:

```tsx
message.role === 'user'
  ? 'bg-slate-100 text-slate-900 rounded-2xl rounded-br-md border border-slate-200 shadow-sm dark:bg-slate-800 dark:text-slate-100 dark:border-slate-700'
  : 'bg-white text-slate-900 dark:bg-gray-900 dark:text-slate-100 rounded-2xl rounded-bl-md shadow-sm border border-slate-200 dark:border-gray-700'
```

- [ ] **Step 2: Tune prose classes**

Use neutral prose classes:

```tsx
message.role === 'user'
  ? 'prose-slate'
  : 'prose-slate dark:prose-invert'
```

- [ ] **Step 3: Replace citation card styling**

Add `data-testid="citation-card"` to each citation card and replace broad blue styling with:

```tsx
className="bg-white rounded-xl border border-slate-200 hover:border-slate-300 transition-all hover:shadow-sm overflow-hidden dark:bg-gray-900 dark:border-gray-700 dark:hover:border-gray-600"
```

Keep the citation number badge blue:

```tsx
className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded-full flex-shrink-0"
```

Use pale blue only for compact relevance metadata:

```tsx
className="text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-100 px-2 py-1 rounded-full dark:text-blue-200 dark:bg-blue-950 dark:border-blue-900"
```

- [ ] **Step 4: Run the focused test**

Run: `npm test -- ChatInterface.test.tsx --run`

Expected: PASS for all `ChatInterface` tests.

### Task 3: Verify Build and Screenshot

**Files:**
- No planned code edits.
- Uses generated runtime output only.

**Interfaces:**
- Consumes: Built frontend assets and Vite dev server.
- Produces: Automated test/build evidence and visual inspection evidence.

- [ ] **Step 1: Run frontend build**

Run: `npm run build`

Expected: TypeScript and Vite build exit 0.

- [ ] **Step 2: Start dev server**

Run: `npm run dev -- --host 127.0.0.1 --port 3000`

Expected: Vite reports a local URL on `http://127.0.0.1:3000/`.

- [ ] **Step 3: Capture or inspect the Workbench**

Open the local URL, create or seed messages if needed, and verify visually:

- User message is light gray/blue-gray with dark text.
- Assistant message is a white reading paper.
- Citation card is neutral with only small blue badge/action accents.
- Active mode tab and send button remain blue.

- [ ] **Step 4: Stop dev server**

Stop the running Vite process after screenshot inspection.
