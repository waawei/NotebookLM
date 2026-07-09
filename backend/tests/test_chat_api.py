import asyncio
import json
import os
import tempfile
import unittest

import httpx
from fastapi import HTTPException
from openai import RateLimitError

from api import chat
from models.chat import ChatRequest
from services.chat_service import ChatService
from services.document_metadata_store import DocumentMetadataStore


class FakeLLM:
    def __init__(self, answer):
        self.answer = answer

    async def generate(self, prompt):
        return self.answer


class FakeStreamingLLM(FakeLLM):
    async def generate_stream(self, prompt):
        yield self.answer


class FakeLLMFactory:
    def __init__(self, clients):
        self.clients = list(clients)
        self.calls = 0

    def __call__(self):
        client = self.clients[self.calls]
        self.calls += 1
        return client


class FakeRetrieval:
    async def retrieve(self, question, doc_ids, top_k):
        return [{"content": "source"}]

    def build_context(self, results):
        return "source"

    def build_citations(self, results):
        return []


class FailingChatService:
    async def ask_stream(self, **kwargs):
        raise RateLimitError(
            "request failed",
            response=httpx.Response(
                429,
                request=httpx.Request(
                    "POST", "https://gateway.test/v1/chat/completions"
                ),
            ),
            body={
                "error": {
                    "message": "Bearer saved-secret at https://gateway.test/reset"
                }
            },
        )
        yield {}


class FailingConversationService:
    async def list_conversations(self):
        raise RuntimeError("Bearer saved-secret at https://gateway.test/conversations")


async def first_sse_payload(response):
    chunk = await anext(response.body_iterator)
    return json.loads(chunk.removeprefix("data: ").strip())


class ChatApiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = DocumentMetadataStore(os.path.join(self.tempdir.name, "test.db"))
        self.original_chat_service = chat.chat_service

    def tearDown(self):
        chat.chat_service = self.original_chat_service
        self.tempdir.cleanup()

    def test_each_chat_generation_uses_a_fresh_factory(self):
        factory = FakeLLMFactory([FakeLLM("first"), FakeLLM("second")])
        service = ChatService(
            retrieval_service=FakeRetrieval(),
            metadata_store=self.store,
            llm_factory=factory,
        )

        first = asyncio.run(service.ask("question", ["doc-1"]))
        second = asyncio.run(service.ask("question", ["doc-1"]))

        self.assertEqual(first.answer, "first")
        self.assertEqual(second.answer, "second")
        self.assertEqual(factory.calls, 2)

    def test_each_stream_uses_a_fresh_factory(self):
        factory = FakeLLMFactory(
            [FakeStreamingLLM("first"), FakeStreamingLLM("second")]
        )
        service = ChatService(
            retrieval_service=FakeRetrieval(),
            metadata_store=self.store,
            llm_factory=factory,
        )

        async def collect(question):
            return [
                event
                async for event in service.ask_stream(question, ["doc-1"])
            ]

        first = asyncio.run(collect("first question"))
        second = asyncio.run(collect("second question"))

        self.assertIn({"type": "content", "content": "first"}, first)
        self.assertIn({"type": "content", "content": "second"}, second)
        self.assertEqual(factory.calls, 2)

    def test_stream_error_contains_only_safe_diagnostic_fields(self):
        chat.chat_service = FailingChatService()

        response = asyncio.run(
            chat.ask_question_stream(ChatRequest(question="question", doc_ids=["doc-1"]))
        )
        payload = asyncio.run(first_sse_payload(response))

        self.assertEqual(payload["type"], "error")
        self.assertEqual(
            payload["message"],
            "The response could not be generated. Check the LLM connection in Settings and try again.",
        )
        self.assertEqual(payload["diagnostic"]["status_code"], 429)
        self.assertEqual(payload["diagnostic"]["category"], "rate_limited")
        self.assertNotIn("saved-secret", json.dumps(payload))
        self.assertNotIn("gateway.test", json.dumps(payload))

    def test_conversation_errors_do_not_return_raw_exception_details(self):
        chat.chat_service = FailingConversationService()

        with self.assertRaises(HTTPException) as raised:
            asyncio.run(chat.list_conversations())

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(
            raised.exception.detail,
            "Conversation history is temporarily unavailable. Please try again.",
        )


if __name__ == "__main__":
    unittest.main()
