import unittest

from services.retrieval_service import RetrievalService


class FakeVectorStore:
    async def search(self, query, doc_ids=None, top_k=None):
        return []


class RetrievalRankingTests(unittest.TestCase):
    def setUp(self):
        self.service = RetrievalService(vector_store=FakeVectorStore())

    def test_exact_title_and_section_matches_move_upward(self):
        results = [
            {
                "content": "General overview text",
                "metadata": {
                    "doc_id": "doc-1",
                    "doc_name": "General Handbook",
                    "section": "Overview",
                    "chunk_id": 1,
                },
                "score": 0.9,
            },
            {
                "content": "Refund policy details",
                "metadata": {
                    "doc_id": "doc-2",
                    "doc_name": "Support Policy",
                    "section": "Refund Policy",
                    "chunk_id": 2,
                },
                "score": 0.4,
            },
        ]

        reranked = self.service.rerank("What is the refund policy?", results)

        self.assertEqual(reranked[0]["metadata"]["doc_id"], "doc-2")

    def test_empty_results_stay_empty(self):
        self.assertEqual(self.service.rerank("anything", []), [])

    def test_reranked_results_preserve_citation_fields(self):
        result = {
            "content": "Claim evidence",
            "metadata": {
                "doc_id": "doc-1",
                "doc_name": "Paper",
                "section": "Findings",
                "page": 2,
                "chunk_id": 4,
            },
            "score": 0.6,
        }

        reranked = self.service.rerank("claim evidence", [result])

        self.assertEqual(reranked[0]["metadata"]["doc_id"], "doc-1")
        self.assertEqual(reranked[0]["metadata"]["doc_name"], "Paper")
        self.assertEqual(reranked[0]["metadata"]["section"], "Findings")
        self.assertEqual(reranked[0]["metadata"]["page"], 2)
        self.assertEqual(reranked[0]["metadata"]["chunk_id"], 4)
        self.assertEqual(reranked[0]["content"], "Claim evidence")


if __name__ == "__main__":
    unittest.main()
