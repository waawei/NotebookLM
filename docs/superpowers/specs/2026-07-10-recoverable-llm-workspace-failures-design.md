# Recoverable LLM Workspace Failure Design

Date: 2026-07-10

## Decision

Make source-grounded work recoverable when an LLM provider cannot generate. Chat, streaming chat, suggested questions, and document summaries resolve a fresh backend LLM configuration at request time. The application returns only structured, sanitized diagnostics across the chat streaming boundary and renders a visible recoverable failure instead of a blank assistant message. Indexed documents retain their successful retrieval state while explicitly recording that an LLM summary is unavailable.

## Goals

1. A Settings save immediately applies to new chat, stream, suggested-question, and summary work without a backend restart.
2. A streaming generation error never creates a blank assistant reply or sends raw exception text to the browser.
3. A user sees a clear in-workbench source-selection prompt instead of a browser alert.
4. A document that parsed and indexed successfully is visibly different from a document whose processing failed, even when its LLM summary is unavailable.
5. No local fallback answer or fabricated summary is generated while the LLM connection is unavailable.

## Root Causes Addressed

- DocumentService and ChatService currently hold an LLMService constructed at backend module initialization, so they can keep stale saved settings.
- Document summary failure is caught and stored as the literal text Summary generation failed while the document status remains completed.
- The streaming API serializes str(exception), and ChatInterface throws that event inside a catch that treats it as a parse error, leaving an empty assistant message.
- The source-selection guard currently uses browser alert and does not offer a persistent in-workbench recovery action.

## Data Model

Add non-secret document summary state:

- summary_status: pending, available, or unavailable.
- summary remains null when unavailable; no failure literal is stored in summary.
- summary_error is a fixed safe label, LLM summary unavailable, when the index succeeded but summary generation could not complete.
- status remains completed when parsing, chunking, and vector indexing succeeded.
- status becomes failed only for parse, chunk, vector, or metadata processing failure; its persisted error is a fixed safe label, Document processing failed.

The document API returns summary_status and summary_error. Existing database rows with a non-empty normal summary migrate to available; rows with the legacy literal Summary generation failed migrate to unavailable with a null summary and fixed safe summary_error; other completed rows default to pending.

## Fresh LLM Resolution

ChatService and DocumentService receive an optional llm_factory for tests. Production uses a default factory that constructs LLMService at generation time.

- ChatService creates a new LLM service for ask, ask_stream, and generate_suggested_questions.
- DocumentService creates a new LLM service inside _generate_summary.
- Existing vectors, conversations, and source metadata remain unchanged.

## Safe Streaming Error Contract

On a generation failure, POST /api/chat/ask-stream emits one SSE event:

    {
      "type": "error",
      "message": "The response could not be generated. Check the LLM connection in Settings and try again.",
      "diagnostic": {
        "phase": "chat_completion",
        "status_code": 503,
        "category": "upstream_unavailable",
        "summary": "The upstream service is currently unavailable."
      }
    }

The diagnostic reuses build_connection_diagnostic and the current backend-only API key. It never includes a Base URL, request path, raw body, exception type, Authorization header, API key, traceback, or exception cause. The non-streaming chat and suggested-question endpoints return fixed safe HTTP errors rather than str(exception).

## UI Behavior

- ChatInterface holds a stream diagnostic only in component state.
- It replaces the optimistic blank assistant message with a visible generic assistant failure and a Details disclosure containing phase, status when available, category, and summary.
- The disclosure and failure state clear before a new question and when the component unmounts. They never enter messages persisted in localStorage, Zustand persistence, API URLs, or toast history.
- With zero selected sources, the composer renders an inline error: Select at least one source before asking a question. The send action performs no API request and no browser alert.
- Source cards add a visible Selected marker and checked icon in their selected state.
- An indexed source with summary_status unavailable displays Indexed with LLM summary unavailable; a failed source displays Processing failed. Neither state presents a synthetic summary.

## Scope Boundaries

- No local extractive or generative fallback is added.
- Model discovery and Settings diagnostic behavior are unchanged.
- Agent run persistence/error behavior is unchanged.
- Existing user/assistant answer persistence retains only safe generic failure text, never the diagnostic.

## Verification

1. Backend tests prove fresh factory calls after a simulated settings update, safe summary state on LLM failure, legacy-summary migration, and fixed processing errors.
2. Chat API tests prove SSE error events have the safe schema and no raw fixture secret/URL.
3. Frontend tests prove zero-source inline recovery, stream error replacement/details, no blank assistant reply, and no diagnostic browser storage.
4. Full frontend build/test and backend unittest/compile checks pass.

