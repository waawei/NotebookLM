import unittest

from services.retrieval_service import RetrievalService


class FakeVectorStore:
    async def search(self, query, doc_ids=None, top_k=None):
        return []


class RetrievalServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = RetrievalService(vector_store=FakeVectorStore())

    def test_context_includes_numbered_source_markers(self):
        context = self.service.build_context(
            [
                {
                    "content": "First source text",
                    "metadata": {
                        "doc_id": "doc-1",
                        "doc_name": "Paper A",
                        "page": 3,
                        "chunk_id": 10,
                    },
                    "score": 0.91,
                },
                {
                    "content": "Second source text",
                    "metadata": {
                        "doc_id": "doc-2",
                        "doc_name": "Paper B",
                        "page": 5,
                        "chunk_id": 11,
                    },
                    "score": 0.82,
                },
            ]
        )

        self.assertIn("[Source 1]", context)
        self.assertIn("[Source 2]", context)
        self.assertIn("First source text", context)
        self.assertIn("Second source text", context)

    def test_citations_preserve_source_fields(self):
        citations = self.service.build_citations(
            [
                {
                    "content": "Evidence about the claim",
                    "metadata": {
                        "doc_id": "doc-1",
                        "doc_name": "Research Notes",
                        "page": 7,
                        "chunk_id": 4,
                    },
                    "score": 0.87,
                }
            ]
        )

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].doc_id, "doc-1")
        self.assertEqual(citations[0].doc_name, "Research Notes")
        self.assertEqual(citations[0].page, 7)
        self.assertEqual(citations[0].chunk_id, 4)
        self.assertEqual(citations[0].content, "Evidence about the claim")
        self.assertEqual(citations[0].relevance_score, 0.87)

    def test_empty_results_produce_empty_context_and_citations(self):
        self.assertEqual(self.service.build_context([]), "")
        self.assertEqual(self.service.build_citations([]), [])


if __name__ == "__main__":
    unittest.main()
