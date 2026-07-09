import os
import tempfile
import unittest

from services.document_metadata_store import DocumentMetadataStore


class ConversationStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        self.store = DocumentMetadataStore(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_conversation_lifecycle_survives_reopen(self):
        conversation = {
            "conversation_id": "conv-1",
            "title": "Thesis notes",
            "created_at": "2026-07-09T00:00:00",
            "updated_at": "2026-07-09T00:01:00",
            "messages": [
                {
                    "message_id": "msg-1",
                    "role": "user",
                    "content": "What is the thesis?",
                    "citations": [],
                    "created_at": "2026-07-09T00:00:00",
                },
                {
                    "message_id": "msg-2",
                    "role": "assistant",
                    "content": "The thesis is about source persistence.",
                    "citations": [{"doc_id": "doc-1", "chunk_id": 2}],
                    "created_at": "2026-07-09T00:01:00",
                },
            ],
        }

        self.store.save_conversation(conversation)

        reopened = DocumentMetadataStore(self.db_path)
        conversations = reopened.list_conversations()
        loaded = reopened.get_conversation("conv-1")

        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0]["conversation_id"], "conv-1")
        self.assertEqual(conversations[0]["title"], "Thesis notes")
        self.assertEqual(conversations[0]["message_count"], 2)
        self.assertEqual(loaded["conversation_id"], "conv-1")
        self.assertEqual(loaded["messages"][1]["role"], "assistant")
        self.assertEqual(loaded["messages"][1]["citations"][0]["doc_id"], "doc-1")

        self.assertTrue(reopened.delete_conversation("conv-1"))
        self.assertIsNone(reopened.get_conversation("conv-1"))
        self.assertEqual(reopened.list_conversations(), [])
        self.assertFalse(reopened.delete_conversation("conv-1"))


if __name__ == "__main__":
    unittest.main()
