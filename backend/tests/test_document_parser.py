import unittest

from services.document_parser import DocumentParser


class DocumentParserChunkTests(unittest.TestCase):
    def setUp(self):
        self.parser = DocumentParser()

    def test_markdown_headings_create_chunks_with_section_names(self):
        chunks = self.parser.chunk_text(
            "# Overview\n"
            "The project stores source material.\n\n"
            "## Evidence\n"
            "The system keeps citations attached to answers."
        )

        self.assertEqual(chunks[0]["section"], "Overview")
        self.assertEqual(chunks[0]["chunk_index"], 0)
        self.assertIn("project stores source", chunks[0]["content"])
        self.assertEqual(chunks[1]["section"], "Evidence")
        self.assertEqual(chunks[1]["chunk_index"], 1)
        self.assertIn("citations", chunks[1]["content"])

    def test_repeated_blank_lines_create_chunks_without_section_names(self):
        chunks = self.parser.chunk_text(
            "First standalone note.\n\n\n"
            "Second standalone note."
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["section"], None)
        self.assertEqual(chunks[1]["section"], None)
        self.assertEqual(chunks[0]["chunk_index"], 0)
        self.assertEqual(chunks[1]["chunk_index"], 1)


if __name__ == "__main__":
    unittest.main()
