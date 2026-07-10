import unittest
import os

os.environ["DEBUG"] = "True"
from core.config import Settings


class SettingsDefaultTests(unittest.TestCase):
    def test_defaults_target_local_ollama(self):
        settings = Settings(_env_file=None)

        self.assertEqual(settings.LLM_PROVIDER, "ollama")
        self.assertEqual(settings.LLM_MODEL, "qwen3:8b")
        self.assertEqual(settings.LLM_BASE_URL, "http://localhost:11434")
        self.assertEqual(settings.LLM_API_KEY, "")


if __name__ == "__main__":
    unittest.main()
