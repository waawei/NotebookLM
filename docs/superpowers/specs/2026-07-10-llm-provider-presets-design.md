# LLM Provider Presets Design

## Goal

Make Settings accept practical provider presets for local Ollama and DeepSeek so Phase 5 Agent generation can be tested without requiring a custom OpenAI-compatible gateway.

## Scope

This change adds provider compatibility only. It does not change Agent skill prompts, tool permissions, output persistence, or the existing secret-handling boundary.

## Provider Behavior

- `ollama` uses the OpenAI-compatible chat API at `http://localhost:11434/v1` by default.
- `ollama` may run without a user API key; the backend supplies a non-secret placeholder only to satisfy the OpenAI SDK constructor.
- `deepseek` uses the OpenAI-compatible chat API at `https://api.deepseek.com` by default and sends that documented base exactly.
- `openai`, `dashscope`, and `openai_compatible` keep their existing behavior.

## Settings UI

Settings adds explicit `Ollama` and `DeepSeek` provider options. Choosing `Ollama` pre-fills `qwen3:8b`, `http://localhost:11434`, and automatic `/v1` normalization. Choosing `DeepSeek` pre-fills `deepseek-v4-flash`, `https://api.deepseek.com`, and exact endpoint mode.

The API key input remains write-only. Ollama copy states that a key is optional for local use. DeepSeek copy keeps the key requirement clear.

## Security

No provider preset may expose API keys in frontend persisted state, API responses, SQLite Agent runs, logs, or Git. All Settings requests continue to go through `frontend/src/services/api.ts`.

## Testing

Backend tests cover provider validation, warnings, default endpoint resolution, and OpenAI SDK client construction. Frontend tests cover provider preset selection and safe request payloads.
