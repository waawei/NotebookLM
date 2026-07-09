"""
LLM service for OpenAI-compatible chat completions.
"""

from openai import OpenAI

from core.config import settings


def normalize_openai_base_url(base_url: str) -> str:
    """Normalize OpenAI-compatible base URLs to include /v1."""
    normalized = base_url.rstrip("/")
    if not normalized:
        return ""
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


class LLMService:
    """Large language model client wrapper."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
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
                    base_url=normalize_openai_base_url(self.base_url),
                )
            return OpenAI(api_key=self.api_key)

        if self.provider == "openai_compatible":
            if not self.base_url:
                raise ValueError("LLM_BASE_URL is required for openai_compatible provider")
            return OpenAI(
                api_key=self.api_key,
                base_url=normalize_openai_base_url(self.base_url),
            )

        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def generate(self, prompt: str) -> str:
        """Generate a full answer."""
        try:
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
        except Exception as e:
            print(f"LLM call failed: {e}")
            raise e

    async def generate_stream(self, prompt: str):
        """Generate an answer as text chunks."""
        try:
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

        except Exception as e:
            print(f"LLM streaming call failed: {e}")
            raise e

    async def test_connection(self) -> str:
        """Run a minimal completion to validate configured credentials."""
        return await self.generate("Reply with exactly: OK")
