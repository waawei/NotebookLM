import os
import tempfile
import unittest

from services.document_metadata_store import DocumentMetadataStore


class ArtifactStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "artifacts.db")
        self.store = DocumentMetadataStore(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_note_links_survive_reopen(self):
        self.store.save_note_link("note-1", "document", "doc-1")
        self.store.save_note_link("note-1", "conversation", "conv-1")

        reopened = DocumentMetadataStore(self.db_path)
        links = reopened.list_note_links("note-1")

        self.assertEqual(
            links,
            [
                {"source_type": "conversation", "source_id": "conv-1"},
                {"source_type": "document", "source_id": "doc-1"},
            ],
        )

    def test_wiki_page_persistence_survives_reopen(self):
        page = self.store.create_wiki_page(
            "Retrieval Notes",
            "# Retrieval\nSource-grounded notes.",
            ["doc-1", "doc-2"],
        )
        self.assertTrue(
            self.store.update_wiki_page(
                page["page_id"],
                "Retrieval Notes Updated",
                "# Retrieval\nUpdated content.",
            )
        )

        reopened = DocumentMetadataStore(self.db_path)
        pages = reopened.list_wiki_pages()
        loaded = reopened.get_wiki_page(page["page_id"])

        self.assertEqual(len(pages), 1)
        self.assertEqual(loaded["title"], "Retrieval Notes Updated")
        self.assertEqual(loaded["content"], "# Retrieval\nUpdated content.")
        self.assertEqual(loaded["source_doc_ids"], ["doc-1", "doc-2"])

    def test_output_persistence_survives_reopen_and_filters_by_kind(self):
        summary = self.store.create_output(
            "summary",
            "Summary",
            "# Summary\nGrounded summary.",
            ["doc-1"],
        )
        self.store.create_output(
            "quiz",
            "Quiz",
            "# Quiz\nQuestions.",
            ["doc-2"],
        )

        reopened = DocumentMetadataStore(self.db_path)
        summaries = reopened.list_outputs("summary")
        all_outputs = reopened.list_outputs()

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["output_id"], summary["output_id"])
        self.assertEqual(summaries[0]["source_doc_ids"], ["doc-1"])
        self.assertEqual(len(all_outputs), 2)


if __name__ == "__main__":
    unittest.main()
