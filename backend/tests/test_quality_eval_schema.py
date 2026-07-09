import json
import os
import unittest


class QualityEvalSchemaTests(unittest.TestCase):
    def test_quality_cases_match_required_schema(self):
        cases_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "evals",
            "quality_cases.json",
        )

        with open(cases_path, "r", encoding="utf-8") as file:
            cases = json.load(file)

        self.assertGreaterEqual(len(cases), 3)
        seen_case_ids = set()

        for case in cases:
            self.assertIsInstance(case["case_id"], str)
            self.assertNotIn(case["case_id"], seen_case_ids)
            seen_case_ids.add(case["case_id"])
            self.assertIsInstance(case["question"], str)
            self.assertIsInstance(case["doc_ids"], list)
            self.assertIn(case["mode"], {"review", "paper", "knowledge_base"})
            self.assertIsInstance(case["must_cite"], bool)
            self.assertIsInstance(case["expected_terms"], list)
            self.assertTrue(
                all(isinstance(term, str) for term in case["expected_terms"])
            )


if __name__ == "__main__":
    unittest.main()
