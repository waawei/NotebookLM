import asyncio
import unittest

from api import wiki


class FakeWikiService:
    def __init__(self):
        self.pages = {}

    def list_pages(self):
        return list(self.pages.values())

    def create_page(self, title, content, source_doc_ids):
        page = {
            "page_id": "page-1",
            "title": title,
            "content": content,
            "source_doc_ids": source_doc_ids,
            "created_at": "2026-07-09T00:00:00",
            "updated_at": "2026-07-09T00:00:00",
        }
        self.pages[page["page_id"]] = page
        return page

    def get_page(self, page_id):
        return self.pages.get(page_id)

    def update_page(self, page_id, title, content):
        if page_id not in self.pages:
            return False
        self.pages[page_id] = {
            **self.pages[page_id],
            "title": title,
            "content": content,
            "updated_at": "2026-07-09T00:01:00",
        }
        return True

    async def generate_page(self, title, source_doc_ids):
        return self.create_page(title, "# Generated\nGrounded page.", source_doc_ids)

    def export_page(self, page_id):
        page = self.pages.get(page_id)
        if not page:
            return None
        return {
            "filename": "retrieval.md",
            "content_type": "text/markdown",
            "content": page["content"],
        }


class WikiApiTests(unittest.TestCase):
    def setUp(self):
        self.original_service = wiki.wiki_service
        self.fake_service = FakeWikiService()
        wiki.wiki_service = self.fake_service

    def tearDown(self):
        wiki.wiki_service = self.original_service

    def test_create_list_get_update_and_generate_pages(self):
        created = asyncio.run(
            wiki.create_page(
                wiki.WikiPageCreate(
                    title="Retrieval",
                    content="# Retrieval\nNotes.",
                    source_doc_ids=["doc-1"],
                )
            )
        )

        listed = asyncio.run(wiki.list_pages())
        loaded = asyncio.run(wiki.get_page(created["page_id"]))
        updated = asyncio.run(
            wiki.update_page(
                created["page_id"],
                wiki.WikiPageUpdate(
                    title="Retrieval Updated",
                    content="# Retrieval\nUpdated.",
                ),
            )
        )
        generated = asyncio.run(
            wiki.generate_page(
                wiki.WikiPageGenerate(
                    title="Generated",
                    source_doc_ids=["doc-2"],
                )
            )
        )

        self.assertEqual(listed["total"], 1)
        self.assertEqual(loaded["source_doc_ids"], ["doc-1"])
        self.assertEqual(updated["message"], "Wiki page updated successfully")
        self.assertEqual(generated["content"], "# Generated\nGrounded page.")
        self.assertEqual(generated["source_doc_ids"], ["doc-2"])

    def test_export_page_returns_markdown_payload(self):
        created = asyncio.run(
            wiki.create_page(
                wiki.WikiPageCreate(
                    title="Retrieval",
                    content="# Retrieval\nNotes.",
                    source_doc_ids=["doc-1"],
                )
            )
        )

        exported = asyncio.run(wiki.export_page(created["page_id"]))

        self.assertEqual(exported["filename"], "retrieval.md")
        self.assertEqual(exported["content_type"], "text/markdown")
        self.assertEqual(exported["content"], "# Retrieval\nNotes.")


if __name__ == "__main__":
    unittest.main()
