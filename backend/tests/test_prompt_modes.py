import unittest

from services.chat_service import ChatService


class PromptModeTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService.__new__(ChatService)

    def test_review_prompt_asks_for_study_explanation_and_review_questions(self):
        prompt = self.service._build_prompt(
            question="Explain this chapter",
            context="[Source 1]\nChapter notes",
            history=None,
            mode="review",
        )

        self.assertIn("study explanation", prompt)
        self.assertIn("review questions", prompt)

    def test_paper_prompt_asks_for_claims_evidence_counterpoints_and_citation_anchors(self):
        prompt = self.service._build_prompt(
            question="Help outline this paper",
            context="[Source 1]\nResearch notes",
            history=None,
            mode="paper",
        )

        self.assertIn("claims", prompt)
        self.assertIn("evidence", prompt)
        self.assertIn("counterpoints", prompt)
        self.assertIn("citation anchors", prompt)

    def test_knowledge_base_prompt_asks_for_direct_source_grounded_answers(self):
        prompt = self.service._build_prompt(
            question="What is the support policy?",
            context="[Source 1]\nPolicy notes",
            history=None,
            mode="knowledge_base",
        )

        self.assertIn("direct source-grounded answers", prompt)


if __name__ == "__main__":
    unittest.main()
