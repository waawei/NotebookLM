"""Safe, non-persistent diagnostics for failed LLM connection tests."""

import re
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)


_BEARER_TOKEN = re.compile(r"(?i)\bBearer\s+[^\s,;]+")
_URL = re.compile(r"(?i)https?://[^\s'\"]+")
_KEY_LIKE_TOKEN = re.compile(r"(?i)\b(?:sk|rk|key)-[^\s,;]{8,}")
_CONTROL_CHARACTERS = re.compile(r"[\r\n\t]+")
_WHITESPACE = re.compile(r"\s+")


def build_connection_diagnostic(error: Exception, api_key: str) -> dict[str, str | int | None]:
    """Return the permitted diagnostic fields for a failed chat-completion probe."""
    category, fallback_summary = _classify(error)
    status_code = getattr(error, "status_code", None)
    provider_message = _provider_message(error)
    summary = sanitize_connection_summary(provider_message or fallback_summary, api_key)

    return {
        "phase": "chat_completion",
        "status_code": status_code if isinstance(status_code, int) else None,
        "category": category,
        "summary": summary,
    }


def sanitize_connection_summary(value: str, api_key: str, limit: int = 280) -> str:
    """Remove secrets and request locations from a short display-only summary."""
    summary = str(value)
    if api_key:
        summary = summary.replace(api_key, "***")
    summary = _BEARER_TOKEN.sub("Bearer ***", summary)
    summary = _URL.sub("[redacted URL]", summary)
    summary = _KEY_LIKE_TOKEN.sub("***", summary)
    summary = _CONTROL_CHARACTERS.sub(" ", summary)
    summary = _WHITESPACE.sub(" ", summary).strip()
    return summary[:limit].rstrip()


def _classify(error: Exception) -> tuple[str, str]:
    if isinstance(error, APITimeoutError):
        return "timed_out", "The upstream request timed out."
    if isinstance(error, AuthenticationError):
        return "authentication_failed", "The upstream rejected the configured API key."
    if isinstance(error, PermissionDeniedError):
        return "permission_denied", "The configured key is not allowed to use this model or endpoint."
    if isinstance(error, NotFoundError):
        return "model_not_found", "The selected model or Chat Completions endpoint was not found."
    if isinstance(error, BadRequestError):
        return "invalid_request", "The upstream rejected the Chat Completions request."
    if isinstance(error, RateLimitError):
        return "rate_limited", "The upstream request was rate limited."
    if isinstance(error, InternalServerError):
        return "upstream_unavailable", "The upstream service is currently unavailable."
    if isinstance(error, APIStatusError) and getattr(error, "status_code", 0) >= 500:
        return "upstream_unavailable", "The upstream service is currently unavailable."
    if isinstance(error, APIConnectionError):
        return "connection_failed", "Could not connect to the upstream service."
    return "unknown", "No safe upstream summary was available."


def _provider_message(error: Exception) -> str:
    if not isinstance(error, APIStatusError):
        return ""

    body: Any = getattr(error, "body", None)
    if not isinstance(body, dict):
        return ""

    nested_error = body.get("error")
    if isinstance(nested_error, dict) and isinstance(nested_error.get("message"), str):
        return nested_error["message"]
    if isinstance(body.get("message"), str):
        return body["message"]
    return ""

