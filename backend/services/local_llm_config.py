"""Safe local persistence and resolution for user-managed LLM settings."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, Literal, Optional
from urllib.parse import urlparse

from core.config import settings


SUPPORTED_PROVIDERS = {"openai", "dashscope", "openai_compatible"}
EndpointMode = Literal["auto", "exact"]
SUPPORTED_ENDPOINT_MODES = {"auto", "exact"}
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "data" / "llm_config.json"


@dataclass(frozen=True)
class EffectiveLLMConfig:
    """The current resolved configuration, including its backend-only key."""

    provider: str
    model: str
    base_url: str
    api_key: str
    temperature: float
    max_tokens: int
    endpoint_mode: EndpointMode = "auto"


class LocalLLMConfigStore:
    """Persist an LLM overlay in the existing Git-ignored backend data directory."""

    def __init__(self, path: str | Path = DEFAULT_CONFIG_PATH):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Local LLM configuration could not be loaded") from exc

        if not isinstance(data, dict):
            raise ValueError("Local LLM configuration is invalid")
        return data

    def save(self, values: dict) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            temporary_path.write_text(
                json.dumps(values, ensure_ascii=False), encoding="utf-8"
            )
            if os.name != "nt":
                os.chmod(temporary_path, 0o600)
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()
        return values

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()


class LLMConfigurationService:
    """Resolve, validate, and redact the backend-only LLM configuration."""

    def __init__(
        self,
        store: Optional[LocalLLMConfigStore] = None,
        defaults: Optional[SimpleNamespace] = None,
    ):
        self.store = store or LocalLLMConfigStore()
        self.defaults = defaults or settings

    def effective_config(self) -> EffectiveLLMConfig:
        return self._to_effective_config(self.store.load())

    def preview(self, values: dict) -> EffectiveLLMConfig:
        """Resolve a validated request patch without persisting it."""
        if not isinstance(values, dict):
            raise ValueError("LLM configuration must be an object")

        candidate = {**self.store.load(), **self._allowed_values(values)}
        self._validate(candidate)
        return self._to_effective_config(candidate)

    def _to_effective_config(self, overlay: dict) -> EffectiveLLMConfig:
        endpoint_mode = self._string_value(overlay, "endpoint_mode", None).lower()
        if endpoint_mode not in SUPPORTED_ENDPOINT_MODES:
            endpoint_mode = "auto"
        return EffectiveLLMConfig(
            provider=self._string_value(overlay, "provider", "LLM_PROVIDER").lower(),
            model=self._string_value(overlay, "model", "LLM_MODEL"),
            base_url=self._string_value(overlay, "base_url", "LLM_BASE_URL"),
            api_key=self._string_value(overlay, "api_key", "LLM_API_KEY"),
            temperature=float(getattr(self.defaults, "LLM_TEMPERATURE")),
            max_tokens=int(getattr(self.defaults, "LLM_MAX_TOKENS")),
            endpoint_mode=endpoint_mode,
        )

    def save(self, values: dict) -> dict:
        if not isinstance(values, dict):
            raise ValueError("LLM configuration must be an object")

        current = self.store.load()
        allowed_values = self._allowed_values(values)
        candidate = {**current, **allowed_values}
        self._validate(candidate)
        return self.store.save(candidate)

    def clear(self) -> None:
        self.store.clear()

    def safe_status(self) -> dict:
        effective = self.effective_config()
        warnings = self._warnings(effective)
        return {
            "provider": effective.provider,
            "model": effective.model,
            "base_url_configured": bool(effective.base_url),
            "api_key_configured": bool(effective.api_key),
            "temperature": effective.temperature,
            "max_tokens": effective.max_tokens,
            "top_k": int(getattr(self.defaults, "TOP_K_RESULTS")),
            "embedding_model": str(getattr(self.defaults, "EMBEDDING_MODEL")),
            "embedding_device": str(getattr(self.defaults, "EMBEDDING_DEVICE")),
            "endpoint_mode": effective.endpoint_mode,
            "warnings": warnings,
        }

    def sanitize(self, message: str, extra_secrets: Iterable[str] = ()) -> str:
        sanitized = str(message)
        secrets = [self.effective_config().api_key, *extra_secrets]
        for secret in sorted({secret for secret in secrets if secret}, key=len, reverse=True):
            sanitized = sanitized.replace(secret, "***")
        return sanitized

    def _validate(self, values: dict) -> None:
        provider = str(values.get("provider", getattr(self.defaults, "LLM_PROVIDER"))).lower()
        model = str(values.get("model", getattr(self.defaults, "LLM_MODEL"))).strip()
        base_url = str(values.get("base_url", getattr(self.defaults, "LLM_BASE_URL"))).strip()
        endpoint_mode = str(values.get("endpoint_mode", "auto")).lower()

        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError("Unsupported LLM provider")
        if not model:
            raise ValueError("LLM model is required")
        if base_url and not self._is_http_url(base_url):
            raise ValueError("LLM base URL must use HTTP or HTTPS")
        if provider == "openai_compatible" and not base_url:
            raise ValueError("LLM base URL is required for openai_compatible")
        if endpoint_mode not in SUPPORTED_ENDPOINT_MODES:
            raise ValueError("Unsupported LLM endpoint mode")

    def _warnings(self, effective: EffectiveLLMConfig) -> list[str]:
        warnings: list[str] = []
        if effective.provider not in SUPPORTED_PROVIDERS:
            warnings.append("Configured LLM provider is unsupported")
        if not effective.api_key:
            warnings.append("LLM API key is not configured")
        if effective.base_url and not self._is_http_url(effective.base_url):
            warnings.append("Configured LLM base URL is invalid")
        if effective.provider == "openai_compatible" and not effective.base_url:
            warnings.append("LLM base URL is required for openai_compatible")
        return warnings

    def _allowed_values(self, values: dict) -> dict:
        return {
            key: value
            for key, value in values.items()
            if key in {"provider", "model", "base_url", "api_key", "endpoint_mode"}
        }

    def _string_value(self, overlay: dict, key: str, default_name: Optional[str]) -> str:
        value = overlay.get(key, getattr(self.defaults, default_name) if default_name else "")
        return value if isinstance(value, str) else str(value)

    @staticmethod
    def _is_http_url(value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
