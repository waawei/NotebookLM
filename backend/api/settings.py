"""Safe, write-only local LLM configuration APIs."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.llm_service import LLMService
from services.local_llm_config import LLMConfigurationService

router = APIRouter()
configuration_service = LLMConfigurationService()


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
    endpoint_mode: str
    warnings: List[str]


class LLMConfigUpdate(BaseModel):
    provider: str
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = Field(default=None, repr=False)
    endpoint_mode: Optional[str] = None


class LLMTestResult(BaseModel):
    ok: bool
    message: str


class LLMModelDiscoveryRequest(BaseModel):
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = Field(default=None, repr=False)
    endpoint_mode: Optional[str] = None


class LLMModelDiscoveryResult(BaseModel):
    models: List[str]


def _safe_status() -> SettingsStatus:
    return SettingsStatus(**configuration_service.safe_status())


@router.get("/status", response_model=SettingsStatus)
async def get_settings_status():
    """Return effective non-secret runtime configuration status."""
    return _safe_status()


@router.put("/llm", response_model=SettingsStatus)
async def save_llm_configuration(update: LLMConfigUpdate):
    """Save a local write-only LLM configuration overlay."""
    try:
        configuration_service.save(update.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid LLM configuration") from exc
    return _safe_status()


@router.delete("/llm", response_model=SettingsStatus)
async def clear_llm_configuration():
    """Remove the local overlay and fall back to compatible .env defaults."""
    configuration_service.clear()
    return _safe_status()


@router.post("/test-llm", response_model=LLMTestResult)
async def test_llm_connection():
    """Validate the current configuration without exposing provider details."""
    if _safe_status().warnings:
        return LLMTestResult(ok=False, message="LLM configuration needs attention")

    try:
        service = LLMService(configuration_service.effective_config())
        await service.test_connection()
        return LLMTestResult(ok=True, message="LLM connection succeeded")
    except Exception:
        return LLMTestResult(
            ok=False,
            message="LLM connection failed. Check provider, model, endpoint, and API key.",
        )


@router.post("/models", response_model=LLMModelDiscoveryResult)
async def list_llm_models(request: LLMModelDiscoveryRequest):
    """List provider model IDs from a non-persisted settings preview."""
    try:
        config = configuration_service.preview(request.model_dump(exclude_none=True))
        return LLMModelDiscoveryResult(models=LLMService(config).list_models())
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to load available models. Check the provider, endpoint, and API key.",
        ) from exc
