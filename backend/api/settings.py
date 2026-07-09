"""
Safe settings API.
"""

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from core.config import settings
from services.llm_service import LLMService

router = APIRouter()


class SettingsStatus(BaseModel):
    provider: str
    model: str
    base_url_configured: bool
    api_key_configured: bool
    temperature: float
    max_tokens: int
    top_k: int
    embedding_model: str
    embedding_device: str
    warnings: List[str]


class LLMTestResult(BaseModel):
    ok: bool
    message: str


def _config_warnings() -> List[str]:
    warnings: List[str] = []
    provider = settings.LLM_PROVIDER.lower()
    supported_providers = {"openai", "dashscope", "openai_compatible"}

    if provider not in supported_providers:
        warnings.append(f"Unsupported provider: {settings.LLM_PROVIDER}")

    if not settings.LLM_API_KEY:
        warnings.append("LLM_API_KEY is not configured")

    if provider == "openai_compatible" and not settings.LLM_BASE_URL:
        warnings.append("LLM_BASE_URL is required for openai_compatible provider")

    return warnings


def _sanitize_error(message: str) -> str:
    if settings.LLM_API_KEY:
        message = message.replace(settings.LLM_API_KEY, "***")
    return message


@router.get("/status", response_model=SettingsStatus)
async def get_settings_status():
    """Return non-secret runtime configuration status."""
    return SettingsStatus(
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
        base_url_configured=bool(settings.LLM_BASE_URL),
        api_key_configured=bool(settings.LLM_API_KEY),
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        top_k=settings.TOP_K_RESULTS,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_device=settings.EMBEDDING_DEVICE,
        warnings=_config_warnings(),
    )


@router.post("/test-llm", response_model=LLMTestResult)
async def test_llm_connection():
    """Validate the configured LLM without exposing credentials."""
    warnings = _config_warnings()
    if warnings:
        return LLMTestResult(ok=False, message="; ".join(warnings))

    try:
        service = LLMService()
        await service.test_connection()
        return LLMTestResult(ok=True, message="LLM connection succeeded")
    except Exception as exc:
        return LLMTestResult(ok=False, message=_sanitize_error(str(exc)))
