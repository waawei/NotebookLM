import asyncio
import unittest

from api import settings
from services.local_llm_config import EffectiveLLMConfig


SAFE_STATUS = {
    "provider": "openai",
    "model": "gpt-test",
    "base_url_configured": False,
    "api_key_configured": True,
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_k": 5,
    "embedding_model": "embedding-model",
    "embedding_device": "cpu",
    "warnings": [],
}


class FakeConfigurationService:
    def __init__(self):
        self.saved = []
        self.cleared = False

    def save(self, values):
        self.saved.append(values)

    def clear(self):
        self.cleared = True

    def safe_status(self):
        return SAFE_STATUS

    def effective_config(self):
        return EffectiveLLMConfig(
            provider="openai",
            model="gpt-test",
            base_url="",
            api_key="saved-secret",
            temperature=0.7,
            max_tokens=2000,
        )

    def sanitize(self, message, extra_secrets=()):
        result = str(message)
        for secret in ["saved-secret", *extra_secrets]:
            result = result.replace(secret, "***")
        return result


class FailingLLMService:
    def __init__(self, config):
        self.config = config

    async def test_connection(self):
        raise RuntimeError("upstream rejected saved-secret")


class SettingsApiTests(unittest.TestCase):
    def setUp(self):
        self.original_configuration_service = settings.configuration_service
        self.original_llm_service = settings.LLMService
        self.configuration_service = FakeConfigurationService()
        settings.configuration_service = self.configuration_service

    def tearDown(self):
        settings.configuration_service = self.original_configuration_service
        settings.LLMService = self.original_llm_service

    def test_save_returns_safe_status_without_api_key(self):
        response = asyncio.run(
            settings.save_llm_configuration(
                settings.LLMConfigUpdate(
                    provider="openai",
                    model="gpt-test",
                    base_url="",
                    api_key="do-not-return",
                )
            )
        )

        self.assertEqual(self.configuration_service.saved[0]["api_key"], "do-not-return")
        self.assertTrue(response.api_key_configured)
        self.assertNotIn("api_key", response.model_dump())
        self.assertNotIn("do-not-return", str(response))

    def test_save_omits_an_unchanged_base_url(self):
        asyncio.run(
            settings.save_llm_configuration(
                settings.LLMConfigUpdate(
                    provider="openai",
                    model="gpt-test",
                    api_key="do-not-return",
                )
            )
        )

        self.assertNotIn("base_url", self.configuration_service.saved[0])

    def test_clear_returns_safe_status(self):
        response = asyncio.run(settings.clear_llm_configuration())

        self.assertTrue(self.configuration_service.cleared)
        self.assertEqual(response.provider, "openai")
        self.assertNotIn("saved-secret", str(response))

    def test_connection_failure_does_not_return_provider_error_or_key(self):
        settings.LLMService = FailingLLMService

        result = asyncio.run(settings.test_llm_connection())

        self.assertFalse(result.ok)
        self.assertEqual(
            result.message,
            "LLM connection failed. Check provider, model, endpoint, and API key.",
        )
        self.assertNotIn("saved-secret", result.message)


if __name__ == "__main__":
    unittest.main()
