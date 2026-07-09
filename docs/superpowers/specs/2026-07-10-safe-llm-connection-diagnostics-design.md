# Safe LLM Connection Diagnostics Design

Date: 2026-07-10

## Decision

When a Settings connection test fails, return a structured, short-lived diagnostic object in addition to the existing generic failure message. The object helps a local user distinguish an unsupported Chat Completions endpoint, authorization issue, model mismatch, rate limit, or network failure without revealing API keys, raw response bodies, URLs, or upstream stack details.

## Goals

1. Explain why model discovery can succeed while Chat Completions fails.
2. Make a failed connection test actionable with phase, HTTP status, category, and a safe short summary.
3. Preserve the project-wide write-only key and no-secret-persistence guarantees.
4. Keep Agent-run failures generic and persisted diagnostics-free.

## Rejected Alternatives

- Continue with only a fixed generic failure message: safest but insufficient for endpoint/model diagnosis.
- Return the raw upstream body or exception string: rejected because gateways can include Key-like values, request URLs, or internal details.
- Persist diagnostics with configuration or Agent runs: rejected because these results can contain provider-specific operational information and become stale.

## Backend Contract

Extend LLMTestResult with an optional diagnostic object present only on a failed connection test:

    {
      "ok": false,
      "message": "LLM connection failed. Check provider, model, endpoint, and API key.",
      "diagnostic": {
        "phase": "chat_completion",
        "status_code": 429,
        "category": "rate_limited",
        "summary": "The upstream request was rate limited."
      }
    }

The result must not include a Base URL, request path, response body, exception type, API key, authorization header, model-list payload, or traceback.

### Diagnostic Fields

- phase: exactly chat_completion for the current Test connection request.
- status_code: an integer from an HTTP provider error, otherwise null.
- category: one of authentication_failed, permission_denied, model_not_found, invalid_request, rate_limited, upstream_unavailable, connection_failed, timed_out, or unknown.
- summary: an actionable, sanitized string no longer than 280 Unicode characters.

Known OpenAI SDK exception types map directly:

- AuthenticationError -> authentication_failed
- PermissionDeniedError -> permission_denied
- NotFoundError -> model_not_found
- BadRequestError -> invalid_request
- RateLimitError -> rate_limited
- InternalServerError and other HTTP 5xx -> upstream_unavailable
- APITimeoutError -> timed_out
- APIConnectionError -> connection_failed
- other exceptions -> unknown

For known exceptions, use safe application-written summaries. For an HTTP error that has a usable provider message, it may supplement the summary only after sanitization and truncation. Unknown exception text is never exposed.

## Sanitization

A new backend-only diagnostic sanitizer operates before the object is returned. It replaces:

- the current effective API key;
- any current submitted temporary key passed to the sanitizer;
- Bearer token values;
- all URLs, including their query and fragment values;
- common key-like tokens, including strings beginning sk-, rk-, and key- with at least eight following non-whitespace characters.

It removes CR/LF control characters, trims whitespace, and truncates to 280 characters. It must not log the original exception or raw response. It must not attach an exception cause to the public HTTP response.

## UI Behavior

The Settings panel keeps diagnostic state only in React component memory.

On a failed Test connection, it displays the existing red feedback plus a compact expandable Details section containing labelled phase, HTTP status where present, category, and summary. It is cleared before every new status load, save, clear, model-discovery, or connection-test action and disappears when the Settings component unmounts. The UI never stores it in localStorage, sessionStorage, Zustand, URL parameters, or a toast history.

## Scope Boundaries

- POST /api/settings/test-llm is the only endpoint changed.
- Model discovery keeps its current fixed failure response and no exception chain.
- Agent run persistence and errors remain generic and do not receive diagnostic data.
- The client continues to use frontend/src/services/api.ts.

## Verification

1. Backend unit tests cover each known category, status-code extraction, 280-character limit, and removal of saved keys, Bearer tokens, query strings, and key-like values.
2. API tests prove the test endpoint exposes only the diagnostic schema on failure and never an exception cause or raw fixture secret.
3. Frontend tests prove a failed diagnostic renders in the Settings component, clears before retry, and is not stored in browser storage.
4. Full frontend build/test and backend unittest/compile checks pass.
