import unittest

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


if __name__ == "__main__":
    unittest.main()
