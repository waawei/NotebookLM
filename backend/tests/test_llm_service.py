import unittest

from services.local_llm_config import EffectiveLLMConfig
from services.llm_service import LLMService
from services.llm_service import normalize_openai_base_url


class NormalizeOpenAIBaseURLTests(unittest.TestCase):
    def test_adds_v1_to_root_base_url(self):
        self.assertEqual(
            normalize_openai_base_url("https://muyuan.do"),
            "https://muyuan.do/v1",
        )

    def test_keeps_existing_v1_base_url(self):
        self.assertEqual(
            normalize_openai_base_url("http://localhost:11434/v1"),
            "http://localhost:11434/v1",
        )

    def test_empty_base_url_stays_empty(self):
        self.assertEqual(normalize_openai_base_url(""), "")

    def test_uses_injected_effective_configuration(self):
        service = LLMService(
            EffectiveLLMConfig(
                provider="openai",
                model="configured-model",
                base_url="https://example.test",
                api_key="injected-secret",
                temperature=0.2,
                max_tokens=123,
            )
        )

        self.assertEqual(service.provider, "openai")
        self.assertEqual(service.model, "configured-model")
        self.assertEqual(service.base_url, "https://example.test")
        self.assertEqual(service.api_key, "injected-secret")


if __name__ == "__main__":
    unittest.main()
