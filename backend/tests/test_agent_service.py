import asyncio
import os
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
        self.assertEqual(failed["error"], "LLM unavailable: ***")
        self.assertNotIn("secret-token", failed["steps"][-1]["payload"]["error"])
        self.assertEqual(failed["steps"][-1]["kind"], "error")


if __name__ == "__main__":
    unittest.main()
