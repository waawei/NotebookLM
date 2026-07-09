# Local LLM Settings and Workbench Design

Date: 2026-07-10

## Decision

Extend the existing React/FastAPI application with a local, backend-owned LLM configuration overlay and a denser knowledge-workbench experience. The implementation will reuse the existing Phase 5 Agents and Skills boundaries; it will not copy Reviva source code, assets, or protected implementation details.

The design takes only high-level public-product cues: a persistent local workspace, clear module hierarchy, inspectable work, and restrained feedback. It keeps the project's React, TypeScript, Tailwind, FastAPI, SQLite metadata, and ChromaDB architecture.

## Goals

1. Let a local user configure provider, base URL, model, and API key through Settings.
2. Keep API keys out of browser persistence, API responses, SQLite, logs, error payloads, generated outputs, and Git-tracked files.
3. Make a saved local configuration override compatible `.env` defaults immediately for new LLM calls and survive backend restart.
4. Keep Agent runs inspectable, persistent, and recoverable while preventing secrets from entering run records or steps.
5. Make theme state single-source, fully propagated, and system-aware.
6. Replace the isolated Workbench chat card with a continuous, full-height workspace message flow while retaining source selection, streaming, citations, and mobile behavior.

## Non-Goals

1. No cloud sync, accounts, multi-user configuration, or remote secret manager.
2. No arbitrary skill tools, shell commands, dynamic imports, or user-provided executable instructions.
3. No imitation of Reviva visual assets, source code, typography, or component implementations.
4. No fake Agent status or generated content.

## Local Configuration Architecture

### Storage and precedence

`LocalLLMConfigStore` writes an atomic JSON document below the existing Git-ignored `backend/data/` runtime directory. The file has restrictive best-effort local permissions and is never loaded by the frontend, SQLite metadata store, or application logs.

At LLM client construction, `LLMConfigurationService` merges settings in this order:

1. A complete value stored in the local configuration file.
2. The corresponding legacy `.env` value from `core.config.settings`.
3. Existing application defaults.

The key is write-only from the UI. An omitted key in a save request preserves an existing locally stored key. A clear action removes the stored local API key and, when no `.env` key exists, leaves the provider unconfigured. Deleting the local configuration overlay restores `.env` behavior.

### API surface

All browser requests remain in `frontend/src/services/api.ts`.

| Endpoint | Purpose | Secret handling |
| --- | --- | --- |
| `GET /api/settings/status` | Safe effective status | Returns provider, model, booleans, non-secret tunables, and warnings only. |
| `PUT /api/settings/llm` | Save provider/base URL/model and optional key | Accepts a write-only `api_key`; response is safe status only. |
| `DELETE /api/settings/llm` | Clear local key and overlay | Returns safe status only. |
| `POST /api/settings/test-llm` | Test the current effective configuration | Returns a fixed, sanitized result message only. |

Validation allows `openai`, `dashscope`, and `openai_compatible`. The compatible provider requires a valid HTTP(S) URL. `http://localhost` remains supported for local model gateways. Any provider response, exception, or input echo is sanitized before persistence, logs, responses, toast state, or Agent steps.

### Agent integration

`AgentService` obtains a fresh `LLMService` for each run execution rather than retaining a startup-time credential snapshot. This means newly created runs use the latest saved configuration. Existing run persistence remains limited to source IDs, prompt request, status, safe steps, output ID, and a sanitized error.

Only tools explicitly found in a manifest and registry are callable. The existing `retrieve_sources` and `create_output` tool calls remain the required Paper Planner/Course Reviewer execution path. No registry entry can execute shell commands or resolve arbitrary Python import paths.

## UI and Interaction Design

### Theme source of truth

The Zustand application store owns one `theme` preference: `system`, `light`, or `dark`. It persists only this non-secret preference. A small theme synchronizer resolves `system` through `prefers-color-scheme`, toggles the root `dark` class, and reacts to system changes only while the preference is `system`.

Semantic surface classes, rather than fixed dark sidebar styles, apply to the app shell, module navigation, panels, forms, overlays, and dialogs. Color transitions are short and respect reduced-motion preferences.

### Settings

Settings becomes one reusable content surface for the module view and modal. It displays the safe effective status and a concise form:

1. Provider select.
2. Model and Base URL inputs.
3. Empty, password-type API key input with a write-only label; the field is cleared after every save/test attempt and never populated from status.
4. Save, test, clear-local-configuration, and refresh actions.
5. Sanitized success, warning, and failure messages.

No Settings component writes raw values to localStorage, sessionStorage, Zustand persistence, console output, URLs, or analytics.

### Workbench

The center column becomes a full-height conversation workspace. It has a scrollable continuous message timeline and a composer anchored at the workspace bottom; it does not use a centered decorative chat card. The selected-source control remains above the composer, and the citation inspector remains a sibling right panel. On narrow viewports, the inspector and source controls collapse into accessible drawers without hiding citations or selected source count.

### Agents and Skills

Skills presents manifest name, description, allowed tools, and output kind without configuration data. Starting a run presents only server-backed state. Agents uses a 1500 ms detail poll while a run is `running`, stops on `completed` or `failed`, and shows persisted steps, sanitized error, and an output link. Shared empty, loading, and failure states use the same compact feedback language as the rest of the workbench.

## Error and Security Rules

1. The redaction utility masks current and submitted API key material before a message crosses an API, persistence, UI, or logging boundary.
2. Generic provider failures state what the user can do (verify endpoint, model access, or key) without reproducing upstream response bodies.
3. Only safe status fields may be serialized in Pydantic response models.
4. Tests must cover configuration persistence, clear behavior, precedence, restart reload, redaction, stale-Agent prevention, and forbidden browser persistence.

## Verification Plan

1. Add failing backend tests before each production behavior: local storage, safe status, redaction, config precedence/restart, API endpoints, and fresh Agent configuration.
2. Add failing frontend tests before behavior changes: API methods, write-only settings form, theme propagation, Workbench layout, and 1500 ms Agent polling.
3. Run focused tests after each task and create a separate commit for each independently working task.
4. Run final frontend build, backend unittest discovery, and Python compilation.
5. With a user-entered valid local credential, prove connection test plus persisted `paper_plan` and `review_cards` Agent outputs across backend restart. Invalid credentials must produce only sanitized failures.

## Acceptance Mapping

| Requirement | Evidence |
| --- | --- |
| Local persisted configuration | Restart test plus ignored runtime file inspection. |
| No API key exposure | API schema tests, redaction tests, frontend tests, and tracked-file search. |
| Fresh Agent configuration | Test that each execution constructs from current configuration. |
| Inspectable, recoverable runs | Existing store restart tests extended with safe error/output assertions. |
| Synchronized theme | Store/UI tests and visual manual check of shell, navigation, panels, forms, and dialogs. |
| Continuous Workbench | Component tests, production build, and manual mobile/desktop check. |
| Real generation | Manual test evidence using valid local user configuration; account quota errors are not success evidence. |
