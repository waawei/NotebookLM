"""
LLM service for OpenAI-compatible chat completions.
"""

from openai import OpenAI

from services.local_llm_config import EndpointMode, EffectiveLLMConfig, LLMConfigurationService


def normalize_openai_base_url(base_url: str, endpoint_mode: EndpointMode = "auto") -> str:
    """Normalize OpenAI-compatible client base URLs according to the selected mode."""
    normalized = base_url.rstrip("/")
    if not normalized or endpoint_mode == "exact":
        return normalized
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


class LLMService:
    """Large language model client wrapper."""

    def __init__(self, config: EffectiveLLMConfig | None = None):
        effective_config = config or LLMConfigurationService().effective_config()
        self.provider = effective_config.provider.lower()
        self.model = effective_config.model
        self.api_key = effective_config.api_key
        self.base_url = effective_config.base_url
        self.endpoint_mode = effective_config.endpoint_mode
        self.temperature = effective_config.temperature
        self.max_tokens = effective_config.max_tokens
        self.client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self.client is None:
            self.client = self._create_client()
        return self.client

    def _create_client(self) -> OpenAI:
        if self.provider == "dashscope":
            return OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

        if self.provider == "openai":
            if self.base_url:
                return OpenAI(
                    api_key=self.api_key,
                    base_url=normalize_openai_base_url(self.base_url, self.endpoint_mode),
                )
            return OpenAI(api_key=self.api_key)

        if self.provider == "openai_compatible":
            if not self.base_url:
                raise ValueError("LLM_BASE_URL is required for openai_compatible provider")
            return OpenAI(
                api_key=self.api_key,
                base_url=normalize_openai_base_url(self.base_url, self.endpoint_mode),
            )

        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def generate(self, prompt: str) -> str:
        """Generate a full answer."""
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""

    async def generate_stream(self, prompt: str):
        """Generate an answer as text chunks."""
        client = self._get_client()
        stream = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    async def test_connection(self) -> str:
        """Run a minimal completion to validate configured credentials."""
        return await self.generate("Reply with exactly: OK")

    def list_models(self) -> list[str]:
        """Return sorted, deduplicated model identifiers from the configured provider."""
        response = self._get_client().models.list()
        model_ids = [getattr(item, "id", "") for item in response.data]
        return sorted(
            {
                model_id
                for model_id in model_ids
                if isinstance(model_id, str) and model_id.strip()
            }
        )
