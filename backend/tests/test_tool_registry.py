import asyncio
import json
import unittest

from services.tool_registry import ToolRegistry


class FakeRetrievalService:
    async def retrieve(self, question, doc_ids, top_k, history=None):
        return [
            {
                "content": f"Evidence for {question}",
                "metadata": {"doc_id": doc_ids[0] if doc_ids else "doc-1"},
                "score": 0.9,
            }
        ]


class FakeNoteService:
    async def create_note(self, title, content, doc_ids=None, conversation_id=None):
        return "note-1"


class FakeOutputService:
    def create_output(self, kind, title, content, source_doc_ids):
        return {
            "output_id": "output-1",
            "kind": kind,
            "title": title,
            "content": content,
            "source_doc_ids": source_doc_ids,
        }


class SecretBearingValidationOutputService:
    def create_output(self, kind, title, content, source_doc_ids):
        raise ValueError(f"Unsupported output kind: {kind}")


class FakeWikiService:
    def create_page(self, title, content, source_doc_ids):
        return {
            "page_id": "wiki-1",
            "title": title,
            "content": content,
            "source_doc_ids": source_doc_ids,
        }


class ToolRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry(
            retrieval_service=FakeRetrievalService(),
            note_service=FakeNoteService(),
            output_service=FakeOutputService(),
            wiki_service=FakeWikiService(),
        )

    def test_lists_only_safe_tool_schemas(self):
        tools = self.registry.list_tools()

        self.assertEqual(
            {tool["name"] for tool in tools},
            {"retrieve_sources", "create_note", "create_output", "create_wiki_page"},
        )
        self.assertTrue(all("parameters" in tool for tool in tools))
        self.assertNotIn("api_key", json.dumps(tools).lower())
        self.assertNotIn("shell", {tool["name"] for tool in tools})

    def test_rejects_unknown_tool_without_executing_anything(self):
        result = asyncio.run(self.registry.run_tool("shell", {"command": "whoami"}))

        self.assertEqual(result["ok"], False)
        self.assertIn("Unknown tool", result["error"])

    def test_does_not_reflect_secret_like_unknown_tool_name(self):
        sentinel = "SYNTHETIC_SECRET_9f2a"

        result = asyncio.run(self.registry.run_tool(f"unknown-{sentinel}", {}))

        self.assertEqual(result, {"ok": False, "error": "Unknown tool"})
        self.assertNotIn(sentinel, result["error"])

    def test_redacts_secret_like_validation_error_from_registered_tool(self):
        sentinel = "SYNTHETIC_SECRET_9f2a"
        self.registry.output_service = SecretBearingValidationOutputService()

        result = asyncio.run(
            self.registry.run_tool(
                "create_output",
                {
                    "kind": sentinel,
                    "title": "Title",
                    "content": "Content",
                    "source_doc_ids": [],
                },
            )
        )

        self.assertEqual(result, {"ok": False, "error": "Tool parameters are invalid"})
        self.assertNotIn(sentinel, result["error"])

    def test_returns_structured_error_for_unhashable_tool_name(self):
        result = asyncio.run(self.registry.run_tool([], {}))

        self.assertEqual(result, {"ok": False, "error": "Tool name must be a string"})

    def test_returns_structured_success_for_registered_tool(self):
        result = asyncio.run(
            self.registry.run_tool(
                "retrieve_sources",
                {"question": "What is retrieval?", "doc_ids": ["doc-1"]},
            )
        )

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["result"]["sources"][0]["metadata"]["doc_id"], "doc-1")

    def test_returns_structured_error_for_invalid_registered_tool_input(self):
        result = asyncio.run(self.registry.run_tool("create_output", {"title": "Missing fields"}))

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"], "Tool parameters are invalid")


if __name__ == "__main__":
    unittest.main()
