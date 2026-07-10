import asyncio
import unittest

from fastapi import HTTPException

from api import preview


class FakeDocumentService:
    def __init__(self):
        self.metadata_store = self
        self.documents = {
            "doc-1": {
                "doc_id": "doc-1",
                "filename": "Research Brief.pdf",
                "file_type": "pdf",
                "status": "completed",
                "total_chunks": 7,
                "summary": "A safe bounded document summary.",
                "source_path": "D:/secret/local/file.pdf",
            }
        }

    def get_document(self, doc_id):
        return self.documents.get(doc_id)


class FakeWikiService:
    def get_page(self, page_id):
        if page_id != "wiki-1":
            return None
        return {
            "page_id": "wiki-1",
            "title": "Retrieval Notes",
            "content": "# Retrieval\nUseful notes.",
            "source_doc_ids": ["doc-1"],
            "created_at": "2026-07-10T10:00:00",
            "updated_at": "2026-07-10T10:00:00",
        }


class FakeNoteService:
    async def get_note(self, note_id):
        if note_id != "note-1":
            return None
        return {
            "note_id": "note-1",
            "title": "Saved Answer",
            "content": "Reusable answer content.",
            "doc_ids": ["doc-1"],
            "conversation_id": "conv-1",
            "links": [{"source_type": "document", "source_id": "doc-1"}],
            "created_at": "2026-07-10T10:00:00",
            "updated_at": "2026-07-10T10:00:00",
        }


class FakeOutputService:
    def get_output(self, output_id):
        if output_id != "out-1":
            return None
        return {
            "output_id": "out-1",
            "kind": "outline",
            "title": "Chapter Outline",
            "content": "Generated outline content.",
            "source_doc_ids": ["doc-1"],
            "created_at": "2026-07-10T10:00:00",
            "updated_at": "2026-07-10T10:00:00",
        }


class PreviewApiTests(unittest.TestCase):
    def setUp(self):
        self.original_document_service = preview.document_service
        self.original_wiki_service = preview.wiki_service
        self.original_note_service = preview.note_service
        self.original_output_service = preview.output_service
        preview.document_service = FakeDocumentService()
        preview.wiki_service = FakeWikiService()
        preview.note_service = FakeNoteService()
        preview.output_service = FakeOutputService()

    def tearDown(self):
        preview.document_service = self.original_document_service
        preview.wiki_service = self.original_wiki_service
        preview.note_service = self.original_note_service
        preview.output_service = self.original_output_service

    def test_document_preview_returns_safe_typed_metadata(self):
        item = asyncio.run(preview.get_preview("document", "doc-1"))

        self.assertEqual(item["type"], "document")
        self.assertEqual(item["id"], "doc-1")
        self.assertEqual(item["title"], "Research Brief.pdf")
        self.assertEqual(item["content_preview"], "A safe bounded document summary.")
        self.assertEqual(item["metadata"]["status"], "completed")
        self.assertEqual(item["metadata"]["total_chunks"], 7)
        self.assertNotIn("source_path", item["metadata"])
        self.assertNotIn("D:/secret", str(item))

    def test_wiki_note_and_output_previews_include_links(self):
        wiki_item = asyncio.run(preview.get_preview("wiki", "wiki-1"))
        note_item = asyncio.run(preview.get_preview("note", "note-1"))
        output_item = asyncio.run(preview.get_preview("output", "out-1"))

        self.assertEqual(wiki_item["content_preview"], "# Retrieval\nUseful notes.")
        self.assertEqual(wiki_item["links"], [{"type": "document", "id": "doc-1", "title": "doc-1"}])
        self.assertEqual(note_item["title"], "Saved Answer")
        self.assertEqual(note_item["links"], [{"type": "document", "id": "doc-1", "title": "doc-1"}])
        self.assertEqual(output_item["metadata"]["kind"], "outline")
        self.assertEqual(output_item["links"], [{"type": "document", "id": "doc-1", "title": "doc-1"}])

    def test_preview_is_bounded_and_missing_targets_return_404(self):
        preview.output_service = type(
            "LongOutputService",
            (),
            {
                "get_output": lambda self, output_id: {
                    "output_id": output_id,
                    "kind": "summary",
                    "title": "Long Output",
                    "content": "x" * 5000,
                    "source_doc_ids": [],
                    "created_at": "2026-07-10T10:00:00",
                    "updated_at": "2026-07-10T10:00:00",
                }
            },
        )()

        item = asyncio.run(preview.get_preview("output", "long"))
        self.assertEqual(len(item["content_preview"]), 4000)

        with self.assertRaises(HTTPException) as missing:
            asyncio.run(preview.get_preview("wiki", "missing"))
        self.assertEqual(missing.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
