import asyncio
import unittest

from fastapi import HTTPException

from api import modeling
from main import app
from services.approval_service import ApprovalService
from services.modeling_gate_service import ModelingGateService
from services.modeling_project_service import ModelingProjectService
from services.modeling_store import ModelingStore


class FakeProjectService:
    def create_project(self, name, deadline=None):
        if not name.strip():
            raise ValueError("Project name is required")
        return {
            "project_id": "p-1",
            "name": name,
            "deadline": deadline,
            "state": "project_initialized",
        }

    def list_projects(self):
        return [{"project_id": "p-1", "name": "Forecast", "state": "project_initialized"}]

    def get_project(self, project_id):
        return self.list_projects()[0] if project_id == "p-1" else None

    def advance(self, project_id):
        project = self.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        if project_id == "conflict":
            raise ValueError("Cannot advance workflow state: completed")
        return {**project, "state": "problem_parsing"}

    def rollback(self, project_id, reason):
        project = self.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        if reason == "conflict":
            raise ValueError("Cannot roll back workflow state: project_initialized")
        return {**project, "state": "project_initialized"}

    def list_tasks(self, project_id):
        if not self.get_project(project_id):
            raise ValueError("Modeling project not found")
        return [{"task_id": "t-1", "project_id": project_id}]

    def list_runs(self, project_id):
        if not self.get_project(project_id):
            raise ValueError("Modeling project not found")
        return [{"run_id": "r-1", "project_id": project_id}]


class ModelingApiTests(unittest.TestCase):
    def setUp(self):
        self.original = modeling.project_service
        modeling.project_service = FakeProjectService()

    def tearDown(self):
        modeling.project_service = self.original

    def test_creates_lists_and_advances_project(self):
        created = asyncio.run(
            modeling.create_project(modeling.ProjectCreate(name="Forecast", deadline="2026-09-01"))
        )
        listed = asyncio.run(modeling.list_projects())
        advanced = asyncio.run(modeling.advance_project("p-1"))

        self.assertEqual(created["deadline"], "2026-09-01")
        self.assertEqual(listed["total"], 1)
        self.assertEqual(advanced["state"], "problem_parsing")

    def test_get_missing_project_returns_404(self):
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(modeling.get_project("missing"))

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "Modeling project not found")

    def test_create_validation_returns_400(self):
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(modeling.create_project(modeling.ProjectCreate(name="  ")))

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(raised.exception.detail, "Project name is required")

    def test_transition_errors_return_409(self):
        with self.assertRaises(HTTPException) as advance_error:
            asyncio.run(modeling.advance_project("missing"))
        with self.assertRaises(HTTPException) as rollback_error:
            asyncio.run(
                modeling.rollback_project(
                    "missing", modeling.RollbackRequest(reason="Needs revision")
                )
            )

        self.assertEqual(advance_error.exception.status_code, 409)
        self.assertEqual(rollback_error.exception.status_code, 409)

    def test_lists_project_tasks_and_runs(self):
        tasks = asyncio.run(modeling.list_project_tasks("p-1"))
        runs = asyncio.run(modeling.list_project_runs("p-1"))

        self.assertEqual(tasks, {"tasks": [{"task_id": "t-1", "project_id": "p-1"}], "total": 1})
        self.assertEqual(runs, {"runs": [{"run_id": "r-1", "project_id": "p-1"}], "total": 1})

    def test_missing_project_task_and_run_lists_return_404(self):
        with self.assertRaises(HTTPException) as task_error:
            asyncio.run(modeling.list_project_tasks("missing"))
        with self.assertRaises(HTTPException) as run_error:
            asyncio.run(modeling.list_project_runs("missing"))

        self.assertEqual(task_error.exception.status_code, 404)
        self.assertEqual(task_error.exception.detail, "Modeling project not found")
        self.assertEqual(run_error.exception.status_code, 404)
        self.assertEqual(run_error.exception.detail, "Modeling project not found")

    def test_router_is_mounted_under_modeling_api_prefix(self):
        paths = {route.path for route in app.routes}

        self.assertIn("/api/modeling/projects", paths)
        self.assertIn("/api/modeling/projects/{project_id}/advance", paths)

    def test_real_api_service_rejects_advancement_without_gate_artifacts(self):
        with self.subTest("production service is fail-closed"):
            self.assertIsNotNone(self.original.gate_service)

        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            store = ModelingStore(f"{tmp}/modeling.db")
            project = store.create_project("Forecast", "forecast", tmp, None)
            store.update_state(project["project_id"], "problem_parsing")
            modeling.project_service = ModelingProjectService(
                store,
                None,
                gate_service=ModelingGateService(store, ApprovalService(store)),
            )
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(modeling.advance_project(project["project_id"]))

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn("problem_spec", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
