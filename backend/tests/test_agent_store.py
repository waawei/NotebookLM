import os
import tempfile
import unittest

from services.document_metadata_store import DocumentMetadataStore


class AgentStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "agents.db")
        self.store = DocumentMetadataStore(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_agent_run_steps_and_completion_survive_reopen(self):
        run = self.store.create_agent_run(
            "paper_planner",
            {"doc_ids": ["doc-1"], "topic": "retrieval"},
        )
        self.store.append_agent_step(
            run["run_id"],
            {
                "kind": "tool",
                "title": "Retrieved selected sources",
                "payload": {"tool": "retrieve_sources", "source_count": 2},
            },
        )
        self.store.append_agent_step(
            run["run_id"],
            {
                "kind": "generation",
                "title": "Generated paper plan",
                "payload": {"output_kind": "paper_plan"},
            },
        )
        self.store.update_agent_run_status(
            run["run_id"],
            "completed",
            output_id="output-1",
        )

        reopened = DocumentMetadataStore(self.db_path)
        loaded = reopened.get_agent_run(run["run_id"])
        listed = reopened.list_agent_runs()

        self.assertEqual(loaded["skill_id"], "paper_planner")
        self.assertEqual(loaded["status"], "completed")
        self.assertEqual(loaded["input_payload"], {"doc_ids": ["doc-1"], "topic": "retrieval"})
        self.assertEqual(loaded["output_id"], "output-1")
        self.assertIsNone(loaded["error"])
        self.assertEqual([step["step_index"] for step in loaded["steps"]], [0, 1])
        self.assertEqual(loaded["steps"][0]["payload"]["tool"], "retrieve_sources")
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["run_id"], run["run_id"])

    def test_failed_run_persists_visible_error(self):
        run = self.store.create_agent_run("course_reviewer", {"doc_ids": []})

        self.store.update_agent_run_status(
            run["run_id"],
            "failed",
            error="LLM unavailable",
        )

        loaded = self.store.get_agent_run(run["run_id"])
        self.assertEqual(loaded["status"], "failed")
        self.assertEqual(loaded["error"], "LLM unavailable")


if __name__ == "__main__":
    unittest.main()
