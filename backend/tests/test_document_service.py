import asyncio
import os
import tempfile
import unittest
from datetime import datetime

from models.document import DocumentMetadata
from services.document_metadata_store import DocumentMetadataStore
from services.document_service import DocumentService


class FailingLLM:
    async def generate(self, prompt):
        raise RuntimeError("upstream rejected stored-secret")


class WorkingLLM:
    def __init__(self, result):
        self.result = result

    async def generate(self, prompt):
        return self.result


class FakeLLMFactory:
    def __init__(self, clients):
        self.clients = list(clients)
        self.calls = 0

    def __call__(self):
        client = self.clients[self.calls]
        self.calls += 1
        return client


class FakeParser:
    def parse_file(self, path):
        return "source text"

    def chunk_text(self, text):
        return [{"content": text, "chunk_id": 0}]


class FakeVectorStore:
    async def add_documents(self, doc_id, chunks, doc_name):
        return None


class DocumentServiceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = DocumentMetadataStore(os.path.join(self.tempdir.name, "test.db"))
        self.store.upsert_document(
            DocumentMetadata(
                doc_id="doc-1",
                filename="source.pdf",
                file_type="pdf",
                file_size=1,
                upload_time=datetime.now(),
                status="pending",
            ),
            source_path=os.path.join(self.tempdir.name, "source.pdf"),
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_index_success_keeps_completed_when_summary_is_unavailable(self):
        factory = FakeLLMFactory([FailingLLM()])
        service = DocumentService(
            metadata_store=self.store,
            parser=FakeParser(),
            vector_store=FakeVectorStore(),
            llm_factory=factory,
        )

        asyncio.run(service.process_document("doc-1"))
        record = self.store.get_document("doc-1")

        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["summary_status"], "unavailable")
        self.assertEqual(record["summary_error"], "LLM summary unavailable")
        self.assertIsNone(record["summary"])
        self.assertNotIn("stored-secret", str(record))
        self.assertEqual(factory.calls, 1)

    def test_each_summary_uses_a_fresh_llm_factory(self):
        factory = FakeLLMFactory([WorkingLLM("first"), WorkingLLM("second")])
        service = DocumentService(
            parser=FakeParser(),
            vector_store=FakeVectorStore(),
            llm_factory=factory,
        )

        first = asyncio.run(service._generate_summary("source text"))
        second = asyncio.run(service._generate_summary("source text"))

        self.assertEqual(first, ("first", "available", None))
        self.assertEqual(second, ("second", "available", None))
        self.assertEqual(factory.calls, 2)


if __name__ == "__main__":
    unittest.main()
