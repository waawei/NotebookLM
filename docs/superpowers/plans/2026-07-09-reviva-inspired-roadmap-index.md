# Reviva-Inspired Roadmap Index

Date: 2026-07-09

This index groups the execution documents for the Reviva-inspired NotebookLM pivot. Use this file as the goal-level acceptance checklist.

## Product Direction

The project follows this strategy:

1. Learn Reviva's UI and module structure.
2. Keep React, FastAPI, Python RAG, SQLite metadata, and ChromaDB.
3. Do not copy Reviva source code.
4. Keep API keys only in backend `.env`.
5. Build Agents and Skills only after the source, chat, note, output, and answer-quality foundations are stable.

## Execution Order

1. [Phase 1 Shell](2026-07-09-reviva-inspired-phase1-shell.md)
2. [Phase 2 Sources, Spaces, And Persistence](2026-07-09-reviva-inspired-phase2-sources-spaces-persistence.md)
3. [Phase 3 Answer Quality](2026-07-09-reviva-inspired-phase3-answer-quality.md)
4. [Phase 4 Notes, Wiki, And Outputs](2026-07-09-reviva-inspired-phase4-notes-wiki-outputs.md)
5. [Phase 5 Agents And Skills](2026-07-09-reviva-inspired-phase5-agents-skills.md)

## Phase Acceptance Matrix

| Phase | Goal | Acceptance Evidence |
| --- | --- | --- |
| Phase 1 | Reviva-like module shell on current stack | Frontend build passes; shell modules exist; settings remain read-only; branch is pushed |
| Phase 2 | Source library, spaces, and durable workflows | SQLite contains spaces/tags/conversations/jobs; documents can be grouped and filtered; restart keeps source and conversation state |
| Phase 3 | Better answer quality | Evaluation set exists; query rewriting, structured chunks, citation grounding, and reranking/hybrid retrieval are tested |
| Phase 4 | Notes, Wiki, and generated outputs | Notes link to sources/messages; outputs are persisted; Wiki pages can be generated, edited, and regenerated |
| Phase 5 | Agents and Skills | Skill manifests load; tools are registered safely; agent runs are inspectable and produce persisted outputs |

## Global Verification Commands

Run these before claiming any phase complete:

```powershell
cd D:\develop\python\NotebookLM\frontend
npm run build
```

```powershell
cd D:\develop\python\NotebookLM\backend
$env:DEBUG='false'
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

```powershell
cd D:\develop\python\NotebookLM\backend
$env:DEBUG='false'
$files = Get-ChildItem -Recurse -Include *.py | Where-Object { $_.FullName -notmatch '\\venv\\' } | ForEach-Object { $_.FullName }
.\venv\Scripts\python.exe -m py_compile @files
```

## Goal-Level Completion Checklist

- [ ] Phase 1 has the workbench shell and module views.
- [ ] Phase 2 lets users manage 3-5 real files in named spaces.
- [ ] Phase 3 improves answer stability with measurable evaluation cases.
- [ ] Phase 4 turns answers into notes, wiki pages, and reusable outputs.
- [ ] Phase 5 adds inspectable Agents and Skills with safe tool boundaries.
- [ ] API keys are never returned to or stored by the frontend.
- [ ] No Reviva source code has been copied into this repository.
- [ ] Frontend build, backend tests, and backend compile checks pass.
- [ ] The final branch is pushed to GitHub.

