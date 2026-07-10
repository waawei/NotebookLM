import os
import tempfile
import unittest

from services.document_metadata_store import DocumentMetadataStore
from services.output_service import OutputService


class OutputExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = DocumentMetadataStore(os.path.join(self.tmp.name, "outputs.db"))
        self.service = OutputService(
            metadata_store=self.store,
            llm_service=object(),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_export_output_returns_markdown_with_title_and_sources(self):
        output = self.store.create_output(
            "summary",
            "Summary",
            "Generated body.",
            ["doc-1", "doc-2"],
        )

        exported = self.service.export_output(output["output_id"])

        self.assertEqual(exported["filename"], "summary.md")
        self.assertEqual(exported["content_type"], "text/markdown")
        self.assertTrue(exported["content"].startswith("# Summary\n\nGenerated body."))
        self.assertIn("## Sources", exported["content"])
        self.assertIn("- doc-1", exported["content"])
        self.assertIn("- doc-2", exported["content"])

    def test_archive_hides_output_until_archived_filter_and_restore_reactivates(self):
        output = self.store.create_output(
            "summary",
            "Summary",
            "Generated body.",
            ["doc-1"],
        )

        archived = self.service.archive_output(output["output_id"])

        self.assertTrue(archived)
        self.assertEqual(self.service.list_outputs(), [])
        archived_outputs = self.service.list_outputs(include_archived=True)
        self.assertEqual(len(archived_outputs), 1)
        self.assertEqual(archived_outputs[0]["status"], "archived")

        exported = self.service.export_output(output["output_id"])
        self.assertIn("Generated body.", exported["content"])

        restored = self.service.restore_output(output["output_id"])

        self.assertTrue(restored)
        self.assertEqual(self.service.list_outputs()[0]["status"], "active")


if __name__ == "__main__":
    unittest.main()
