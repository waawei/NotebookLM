import os
import tempfile
import unittest

from services.modeling_store import ModelingStore


class ModelingStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = ModelingStore(os.path.join(self.tempdir.name, "modeling.db"))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_project_and_transition_survive_new_store_instance(self):
        project = self.store.create_project("Forecast", "forecast", "D:/safe/forecast", None)
        self.store.record_transition(
            project["project_id"],
            "project_initialized",
            "problem_parsing",
            "advance",
        )
        self.store.update_state(project["project_id"], "problem_parsing")

        reopened = ModelingStore(self.store.db_path)
        loaded = reopened.get_project(project["project_id"])
        self.assertEqual(loaded["state"], "problem_parsing")
        self.assertEqual(len(reopened.list_transitions(project["project_id"])), 1)

    def test_tasks_round_trip_structured_payloads(self):
        project = self.store.create_project("Forecast", "forecast", "D:/safe/forecast", None)
        task = self.store.create_task(
            project["project_id"],
            "problem_parsing",
            "modeling",
            {"prompt": "Forecast sales"},
            ["problem_spec.json"],
        )
        self.store.update_task(task["task_id"], "running", 1)

        [loaded] = self.store.list_tasks(project["project_id"])
        self.assertEqual(loaded["status"], "running")
        self.assertEqual(loaded["retry_count"], 1)
        self.assertEqual(loaded["input_payload"], {"prompt": "Forecast sales"})
        self.assertEqual(loaded["output_requirements"], ["problem_spec.json"])
