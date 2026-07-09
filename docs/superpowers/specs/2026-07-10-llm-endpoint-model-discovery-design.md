# Endpoint Modes and Temporary Model Discovery Design

Date: 2026-07-10

## Decision

Extend the local LLM Settings surface with endpoint-format guidance, a write-only API-key visibility toggle, and model discovery from the current form values. The implementation reuses the existing FastAPI/React application and OpenAI-compatible client; it does not copy CCSwitch source code, assets, or implementation details.

## Goals

1. Make Base URL entry predictable for direct providers and OpenAI-compatible gateways.
2. Let users choose between automatic /v1 normalization and an exact API-base mode.
3. Fetch a model list using saved configuration or unsaved current form values without persisting a temporary API key.
4. Let users temporarily reveal only a key they have typed in the current form session.
5. Preserve the existing rule that saved API keys are never returned, hydrated, logged, or revealed.

## Endpoint Contract

The form exposes an Endpoint format selector.

### Automatic /v1 mode

This is the default. It accepts each of the following inputs:

- https://gateway.example
- https://gateway.example/
- https://gateway.example/v1
- https://gateway.example/v1/

The backend strips trailing slashes and appends /v1 only when the supplied path does not already end in /v1. The user enters an API base, never a resource endpoint such as /chat/completions or /models.

### Exact API base mode

This mode is for a gateway whose documentation specifies a nonstandard OpenAI-compatible base path. The backend strips only trailing slashes and never adds /v1. The OpenAI client still adds resource paths such as /models and /chat/completions.

For a third-party relay or local gateway, the user selects openai_compatible. The direct openai provider can use its default endpoint when Base URL is empty. DashScope retains its built-in compatible endpoint.

## Configuration and Security

endpoint_mode is a non-secret local configuration value stored alongside the saved provider/model/Base URL/API key overlay. It is allowed in safe status responses only as a mode name.

The API key field starts empty every time. Its eye button changes only the HTML input type while the user is editing the current unsaved value. It never fetches a previously saved key, does not preserve the value after save/test/model discovery, and does not write it to browser storage, Zustand, a URL, logs, SQLite, Agent runs, API responses, or tracked files.

Because safe status deliberately does not return a custom Base URL, an existing custom endpoint is represented as configured. Leaving the field untouched preserves it; changing it requires entering a replacement. Clearing the local configuration restores .env fallback.

## Temporary Model Discovery

Add POST /api/settings/models with a request body:

    {
      "provider": "openai_compatible",
      "base_url": "https://gateway.example",
      "endpoint_mode": "auto",
      "api_key": "optional-write-only-temporary-key"
    }

All fields are optional patches. The backend resolves them over the saved local configuration and .env defaults without calling save(). It creates an ephemeral LLMService from the resolved configuration, invokes the OpenAI-compatible models API, returns a deduplicated sorted list of non-empty model IDs, then discards the temporary configuration.

Only model IDs are returned. Invalid input, upstream bodies, and exception strings are not returned. The UI displays a fixed, actionable failure message. The form clears its API-key field after a model discovery attempt whether it succeeds or fails. Model IDs live only in component state and are offered through a datalist; manual model entry remains supported.

## Interfaces

- EndpointMode = "auto" | "exact".
- EffectiveLLMConfig.endpoint_mode: EndpointMode.
- LLMService.list_models() -> list[str].
- LLMConfigurationService.preview(values: dict) -> EffectiveLLMConfig; it validates and merges without disk writes.
- POST /api/settings/models returns { "models": ["model-id"] }.
- settingsApi.listModels(data: SettingsModelDiscoveryRequest) is the only frontend request path.
- SettingsStatus.endpoint_mode contains only "auto" or "exact".

## Verification

1. Backend tests prove automatic mode normalizes all four supported URL forms, exact mode does not append /v1, preview does not create/change the local configuration file, and /models returns only model IDs without serializing the temporary key.
2. Frontend tests prove the form sends a temporary key only to model discovery, clears it afterward, offers returned IDs, and never receives a saved key.
3. Visual checks prove help text explains automatic and exact forms, the eye button applies only to the current input, and model discovery works for manually entered gateway details.
4. Full frontend build/test and backend unittest/compile checks continue to pass.

