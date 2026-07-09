import os
import tempfile
import unittest

from models.document import DocumentMetadata
from services.document_metadata_store import DocumentMetadataStore


class MetadataStorePhase2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        self.store = DocumentMetadataStore(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_space_assignment_and_tag_filtering_survive_reopen(self):
        self.store.upsert_document(
            DocumentMetadata(
                doc_id="doc-1",
                filename="paper.pdf",
                file_type="pdf",
                file_size=100,
                upload_time="2026-07-09T00:00:00",
                status="completed",
                total_chunks=3,
                summary="paper summary",
            )
        )
        space = self.store.create_space("Thesis", "paper writing")
        self.store.assign_document_to_space("doc-1", space["space_id"])
        self.store.set_document_tags("doc-1", ["paper", "review"])

        reopened = DocumentMetadataStore(self.db_path)
        results = reopened.search_documents(
            space_id=space["space_id"], tags=["paper"], status="completed"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["doc_id"], "doc-1")
        self.assertEqual(results[0]["space_id"], space["space_id"])
        self.assertEqual(results[0]["tags"], ["paper", "review"])

    def test_legacy_failed_summary_migrates_to_unavailable_without_literal_content(self):
        self.store.upsert_document(
            DocumentMetadata(
                doc_id="legacy-doc",
                filename="legacy.pdf",
                file_type="pdf",
                file_size=1,
                upload_time="2026-07-10T00:00:00",
                status="completed",
                summary="Summary generation failed.",
            )
        )

        record = DocumentMetadataStore(self.db_path).get_document("legacy-doc")

        self.assertEqual(record["summary_status"], "unavailable")
        self.assertEqual(record["summary_error"], "LLM summary unavailable")
        self.assertIsNone(record["summary"])


if __name__ == "__main__":
    unittest.main()
