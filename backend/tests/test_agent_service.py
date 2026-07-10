import asyncio
import os
import sqlite3
import tempfile
import unittest

from services.agent_service import AgentService
from services.document_metadata_store import DocumentMetadataStore


class FakeSkillService:
    def get_skill(self, skill_id):
        if skill_id != "paper_planner":
            return None
        return {
            "skill_id": "paper_planner",
            "name": "Paper Planner",
            "allowed_tools": ["retrieve_sources", "create_output"],
            "prompt_template": "Create a paper plan grounded in the selected sources.",
            "output_kind": "paper_plan",
        }


class FakeToolRegistry:
    async def run_tool(self, tool_name, params):
        if tool_name == "retrieve_sources":
            return {"ok": True, "result": {"sources": [{"content": "Local evidence"}]}}
        if tool_name == "create_output":
            return {"ok": True, "result": {"output_id": "output-1"}}
        return {"ok": False, "error": "Unexpected tool"}


class FakeLLMService:
    async def generate(self, prompt):
        return "# Paper Plan\n\nGrounded in local evidence."


class FailingLLMService:
    api_key = "secret-token"

    async def generate(self, prompt):
        raise RuntimeError("LLM unavailable: secret-token")


class PromptReflectingFailureLLMService:
    async def generate(self, prompt):
        raise RuntimeError(f"LLM rejected prompt: {prompt}")


class SourceBearingToolRegistry(FakeToolRegistry):
    def __init__(self, source_sentinel):
        self.source_sentinel = source_sentinel

    async def run_tool(self, tool_name, params):
        if tool_name == "retrieve_sources":
            return {
                "ok": True,
                "result": {"sources": [{"content": self.source_sentinel}]},
            }
        return await super().run_tool(tool_name, params)


class SequencedLLMFactory:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return FakeLLMService()


class AgentServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = DocumentMetadataStore(os.path.join(self.tmp.name, "agents.db"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_executes_allowed_tools_and_persists_completed_run(self):
        service = AgentService(
            metadata_store=self.store,
            skill_service=FakeSkillService(),
            tool_registry=FakeToolRegistry(),
            llm_service=FakeLLMService(),
        )

        run = service.create_run("paper_planner", {"doc_ids": ["doc-1"], "request": "Plan it"})
        completed = asyncio.run(service.execute_run(run["run_id"]))

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["output_id"], "output-1")
        self.assertEqual(
            [step["kind"] for step in completed["steps"]],
            ["tool", "generation", "tool"],
        )

    def test_records_failed_run_with_visible_error(self):
        service = AgentService(
            metadata_store=self.store,
            skill_service=FakeSkillService(),
            tool_registry=FakeToolRegistry(),
            llm_service=FailingLLMService(),
        )

        run = service.create_run("paper_planner", {"doc_ids": []})
        failed = asyncio.run(service.execute_run(run["run_id"]))

        self.assertEqual(failed["status"], "failed")
        self.assertEqual(
            failed["error"],
            "Agent run failed. Check your LLM settings and try again.",
        )
        self.assertNotIn("secret-token", failed["steps"][-1]["payload"]["error"])
        self.assertEqual(failed["steps"][-1]["kind"], "error")

    def test_hides_reflected_request_and_source_values_from_failed_run(self):
        request_sentinel = "SYNTHETIC_REQUEST_9f2a"
        source_sentinel = "SYNTHETIC_SOURCE_7c3d"
        service = AgentService(
            metadata_store=self.store,
            skill_service=FakeSkillService(),
            tool_registry=SourceBearingToolRegistry(source_sentinel),
            llm_service=PromptReflectingFailureLLMService(),
        )

        run = service.create_run(
            "paper_planner",
            {"doc_ids": ["doc-1"], "request": request_sentinel},
        )
        failed = asyncio.run(service.execute_run(run["run_id"]))
        error_step = failed["steps"][-1]

        self.assertEqual(failed["status"], "failed")
        self.assertEqual(
            failed["error"],
            "Agent run failed. Check your LLM settings and try again.",
        )
        for sentinel in (request_sentinel, source_sentinel):
            self.assertNotIn(sentinel, failed["error"])
            self.assertNotIn(sentinel, error_step["payload"]["error"])

    def test_each_run_uses_a_fresh_llm_service(self):
        factory = SequencedLLMFactory()
        service = AgentService(
            metadata_store=self.store,
            skill_service=FakeSkillService(),
            tool_registry=FakeToolRegistry(),
            llm_factory=factory,
        )

        self.assertIs(service.llm_factory, factory)

        first = service.create_run("paper_planner", {"doc_ids": []})
        second = service.create_run("paper_planner", {"doc_ids": []})
        asyncio.run(service.execute_run(first["run_id"]))
        asyncio.run(service.execute_run(second["run_id"]))

        self.assertEqual(factory.calls, 2)

    def test_sanitizes_configured_key_in_input_payload_before_persistence(self):
        saved_key = "stored configuration value with spaces"
        service = AgentService(
            metadata_store=self.store,
            skill_service=FakeSkillService(),
            tool_registry=FakeToolRegistry(),
            llm_service=FakeLLMService(),
            error_sanitizer=lambda value: value.replace(saved_key, "***"),
        )

        run = service.create_run(
            "paper_planner",
            {"doc_ids": ["doc-1"], "request": f"Plan using {saved_key}"},
        )
        loaded = service.get_run(run["run_id"])
        conn = sqlite3.connect(self.store.db_path)
        try:
            raw_input = conn.execute(
                "SELECT input_payload_json FROM agent_runs WHERE run_id = ?",
                (run["run_id"],),
            ).fetchone()[0]
        finally:
            conn.close()

        self.assertEqual(loaded["input_payload"]["doc_ids"], ["doc-1"])
        self.assertEqual(loaded["input_payload"]["request"], "Plan using ***")
        self.assertNotIn(saved_key, str(run))
        self.assertNotIn(saved_key, str(loaded))
        self.assertNotIn(saved_key, raw_input)


if __name__ == "__main__":
    unittest.main()
