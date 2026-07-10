import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from services.local_llm_config import LocalLLMConfigStore, LLMConfigurationService


class LocalLLMConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "runtime" / "llm.json"
        self.defaults = SimpleNamespace(
            LLM_PROVIDER="dashscope",
            LLM_MODEL="qwen-turbo",
            LLM_API_KEY="env-secret",
            LLM_BASE_URL="",
            LLM_TEMPERATURE=0.7,
            LLM_MAX_TOKENS=2000,
            TOP_K_RESULTS=5,
            EMBEDDING_MODEL="embedding-model",
            EMBEDDING_DEVICE="cpu",
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def make_service(self):
        return LLMConfigurationService(LocalLLMConfigStore(self.path), self.defaults)

    def test_local_key_overrides_env_and_survives_new_service_instance(self):
        first = self.make_service()
        first.save(
            {
                "provider": "openai_compatible",
                "model": "local-model",
                "base_url": "http://localhost:11434",
                "api_key": "local-secret",
            }
        )

        effective = self.make_service().effective_config()

        self.assertEqual(effective.provider, "openai_compatible")
        self.assertEqual(effective.model, "local-model")
        self.assertEqual(effective.base_url, "http://localhost:11434")
        self.assertEqual(effective.api_key, "local-secret")

    def test_save_without_key_preserves_existing_local_key(self):
        service = self.make_service()
        service.save({"provider": "openai", "model": "first", "api_key": "local-secret"})
        service.save({"provider": "openai", "model": "second", "base_url": ""})

        self.assertEqual(service.effective_config().api_key, "local-secret")
        self.assertEqual(service.effective_config().model, "second")

    def test_clear_restores_env_defaults(self):
        service = self.make_service()
        service.save({"provider": "openai", "model": "local-model", "api_key": "local-secret"})
        service.clear()

        effective = service.effective_config()
        self.assertEqual(effective.provider, "dashscope")
        self.assertEqual(effective.model, "qwen-turbo")
        self.assertEqual(effective.api_key, "env-secret")
        self.assertFalse(self.path.exists())

    def test_safe_status_never_returns_local_key(self):
        service = self.make_service()
        service.save({"provider": "openai", "model": "local-model", "api_key": "local-secret"})

        status = service.safe_status()

        self.assertTrue(status["api_key_configured"])
        self.assertEqual(status["provider"], "openai")
        self.assertNotIn("api_key", status)
        self.assertNotIn("local-secret", str(status))

    def test_sanitize_masks_stored_and_submitted_key(self):
        service = self.make_service()
        service.save({"provider": "openai", "model": "local-model", "api_key": "stored-secret"})

        self.assertEqual(
            service.sanitize("stored-secret submitted-secret", ["submitted-secret"]),
            "*** ***",
        )

    def test_rejects_compatible_provider_without_http_url(self):
        with self.assertRaisesRegex(ValueError, "HTTP"):
            self.make_service().save(
                {
                    "provider": "openai_compatible",
                    "model": "local-model",
                    "base_url": "file:///not-allowed",
                }
            )

    def test_preview_merges_a_temporary_key_without_writing_the_overlay(self):
        service = self.make_service()

        preview = service.preview(
            {
                "provider": "openai_compatible",
                "model": "listed-model",
                "base_url": "https://gateway.test",
                "api_key": "temporary-key",
                "endpoint_mode": "exact",
            }
        )

        self.assertEqual(preview.api_key, "temporary-key")
        self.assertEqual(preview.endpoint_mode, "exact")
        self.assertFalse(self.path.exists())

    def test_safe_status_returns_endpoint_mode_but_never_key(self):
        service = self.make_service()
        service.save(
            {
                "provider": "openai",
                "model": "listed-model",
                "api_key": "stored-key",
                "endpoint_mode": "exact",
            }
        )

        status = service.safe_status()

        self.assertEqual(status["endpoint_mode"], "exact")
        self.assertNotIn("stored-key", str(status))

    def test_ollama_defaults_to_local_openai_compatible_endpoint_without_key_warning(self):
        service = self.make_service()
        service.save({"provider": "ollama", "model": "qwen3:8b"})

        effective = service.effective_config()
        status = service.safe_status()

        self.assertEqual(effective.provider, "ollama")
        self.assertEqual(effective.model, "qwen3:8b")
        self.assertEqual(effective.base_url, "http://localhost:11434")
        self.assertEqual(effective.api_key, "")
        self.assertEqual(effective.endpoint_mode, "auto")
        self.assertFalse(status["api_key_configured"])
        self.assertEqual(status["warnings"], [])

    def test_switching_to_ollama_without_key_clears_previous_local_key(self):
        service = self.make_service()
        service.save(
            {
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "api_key": "previous-provider-secret",
            }
        )
        service.save({"provider": "ollama", "model": "qwen3:8b"})

        effective = service.effective_config()

        self.assertEqual(effective.provider, "ollama")
        self.assertEqual(effective.api_key, "")
        self.assertNotIn("previous-provider-secret", str(service.store.load()))

    def test_deepseek_defaults_to_exact_api_base(self):
        service = self.make_service()
        service.save(
            {
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "api_key": "deepseek-secret",
            }
        )

        effective = service.effective_config()

        self.assertEqual(effective.provider, "deepseek")
        self.assertEqual(effective.model, "deepseek-v4-flash")
        self.assertEqual(effective.base_url, "https://api.deepseek.com")
        self.assertEqual(effective.api_key, "deepseek-secret")
        self.assertEqual(effective.endpoint_mode, "exact")


if __name__ == "__main__":
    unittest.main()
