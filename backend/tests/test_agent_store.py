import os
import sqlite3
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

    def _raw_agent_values(self, run_id):
        conn = sqlite3.connect(self.db_path)
        try:
            run_row = conn.execute(
                "SELECT input_payload_json, error FROM agent_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            step_rows = conn.execute(
                "SELECT payload_json FROM agent_steps WHERE run_id = ?",
                (run_id,),
            ).fetchall()
        finally:
            conn.close()
        return run_row, step_rows

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
        self.assertIsNone(loaded["project_id"])
        self.assertIsNone(loaded["task_id"])
        self.assertIsNone(loaded["stage"])

    def test_modeling_links_round_trip_on_agent_runs(self):
        run = self.store.create_agent_run(
            "modeling_agent",
            {"project": "forecast"},
            project_id="project-1",
            task_id="task-1",
            stage="problem_parsing",
        )

        loaded = self.store.get_agent_run(run["run_id"])
        listed = self.store.list_agent_runs(project_id="project-1")

        self.assertEqual(loaded["project_id"], "project-1")
        self.assertEqual(loaded["task_id"], "task-1")
        self.assertEqual(loaded["stage"], "problem_parsing")
        self.assertEqual([item["run_id"] for item in listed], [run["run_id"]])
        self.assertEqual(self.store.list_agent_runs(project_id="missing"), [])

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

    def test_redacts_sensitive_input_payload_values_before_returning_or_storing(self):
        key_token = "sk-agent-input-0123456789"
        bearer_token = "agent-input-bearer-0123456789"
        run = self.store.create_agent_run(
            "paper_planner",
            {
                "doc_ids": ["doc-1"],
                "request": f"Plan with {key_token} included",
                "connection": {
                    "api_key": key_token,
                    "authorization": f"Bearer {bearer_token}",
                },
            },
        )

        loaded = self.store.get_agent_run(run["run_id"])
        raw_run, raw_steps = self._raw_agent_values(run["run_id"])

        self.assertEqual(loaded["input_payload"]["doc_ids"], ["doc-1"])
        self.assertEqual(loaded["input_payload"]["request"], "Plan with *** included")
        self.assertEqual(
            loaded["input_payload"]["connection"],
            {"api_key": "***", "authorization": "***"},
        )
        self.assertNotIn(key_token, str(loaded))
        self.assertNotIn(bearer_token, str(loaded))
        self.assertNotIn(key_token, raw_run[0])
        self.assertNotIn(bearer_token, raw_run[0])
        self.assertEqual(raw_steps, [])

    def test_redacts_sensitive_step_payload_values_before_returning_or_storing(self):
        key_token = "sk-agent-step-0123456789"
        bearer_token = "agent-step-bearer-0123456789"
        run = self.store.create_agent_run("paper_planner", {"doc_ids": ["doc-1"]})

        self.store.append_agent_step(
            run["run_id"],
            {
                "kind": "tool",
                "title": "Retrieved selected sources",
                "payload": {
                    "tool": "retrieve_sources",
                    "source_count": 2,
                    "connection": {
                        "api_key": key_token,
                        "authorization": f"Bearer {bearer_token}",
                    },
                    "detail": f"Retry using {key_token}",
                },
            },
        )

        loaded = self.store.get_agent_run(run["run_id"])
        raw_run, raw_steps = self._raw_agent_values(run["run_id"])
        payload = loaded["steps"][0]["payload"]

        self.assertEqual(payload["tool"], "retrieve_sources")
        self.assertEqual(payload["source_count"], 2)
        self.assertEqual(payload["detail"], "Retry using ***")
        self.assertEqual(
            payload["connection"],
            {"api_key": "***", "authorization": "***"},
        )
        self.assertNotIn(key_token, str(loaded))
        self.assertNotIn(bearer_token, str(loaded))
        self.assertNotIn(key_token, raw_run[0])
        self.assertNotIn(bearer_token, raw_run[0])
        self.assertNotIn(key_token, raw_steps[0][0])
        self.assertNotIn(bearer_token, raw_steps[0][0])

    def test_redacts_sensitive_failed_error_before_returning_or_storing(self):
        key_token = "sk-agent-error-0123456789"
        bearer_token = "agent-error-bearer-0123456789"
        run = self.store.create_agent_run("paper_planner", {"doc_ids": ["doc-1"]})

        self.store.update_agent_run_status(
            run["run_id"],
            "failed",
            error=f"Provider rejected Bearer {bearer_token}; key {key_token}",
        )

        loaded = self.store.get_agent_run(run["run_id"])
        raw_run, raw_steps = self._raw_agent_values(run["run_id"])

        self.assertEqual(loaded["status"], "failed")
        self.assertEqual(loaded["error"], "Provider rejected Bearer ***; key ***")
        self.assertNotIn(key_token, str(loaded))
        self.assertNotIn(bearer_token, str(loaded))
        self.assertNotIn(key_token, raw_run[0])
        self.assertNotIn(bearer_token, raw_run[0])
        self.assertNotIn(key_token, raw_run[1])
        self.assertNotIn(bearer_token, raw_run[1])
        self.assertEqual(raw_steps, [])

    def test_redacts_compound_sensitive_field_names_before_returning_or_storing(self):
        input_api_key = "opaque input credential value"
        input_authorization = "opaque input authorization value"
        step_secret = "opaque step credential value"
        step_token = "opaque step session value"
        step_password = "opaque step password value"
        run = self.store.create_agent_run(
            "paper_planner",
            {
                "doc_ids": ["doc-1"],
                "model": "test-model",
                "openai_api_key": input_api_key,
                "upstream_authorization": input_authorization,
            },
        )
        self.store.append_agent_step(
            run["run_id"],
            {
                "kind": "tool",
                "title": "Retrieved selected sources",
                "payload": {
                    "tool": "retrieve_sources",
                    "source_count": 2,
                    "client_secret": step_secret,
                    "session_token": step_token,
                    "proxy_password": step_password,
                },
            },
        )

        loaded = self.store.get_agent_run(run["run_id"])
        raw_run, raw_steps = self._raw_agent_values(run["run_id"])
        sentinels = [
            input_api_key,
            input_authorization,
            step_secret,
            step_token,
            step_password,
        ]

        self.assertEqual(loaded["input_payload"]["doc_ids"], ["doc-1"])
        self.assertEqual(loaded["input_payload"]["model"], "test-model")
        self.assertEqual(loaded["input_payload"]["openai_api_key"], "***")
        self.assertEqual(loaded["input_payload"]["upstream_authorization"], "***")
        self.assertEqual(loaded["steps"][0]["payload"]["tool"], "retrieve_sources")
        self.assertEqual(loaded["steps"][0]["payload"]["source_count"], 2)
        self.assertEqual(loaded["steps"][0]["payload"]["client_secret"], "***")
        self.assertEqual(loaded["steps"][0]["payload"]["session_token"], "***")
        self.assertEqual(loaded["steps"][0]["payload"]["proxy_password"], "***")
        for sentinel in sentinels:
            self.assertNotIn(sentinel, str(run))
            self.assertNotIn(sentinel, str(loaded))
            self.assertNotIn(sentinel, raw_run[0])
            self.assertNotIn(sentinel, raw_steps[0][0])


if __name__ == "__main__":
    unittest.main()
