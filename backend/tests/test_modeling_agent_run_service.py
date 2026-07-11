from services.document_metadata_store import DocumentMetadataStore
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_store import ModelingStore
import pytest


def test_agent_run_lifecycle_records_task_run_artifacts_and_completion(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(tmp_path / "workspace"), None)
    agent_store = DocumentMetadataStore(str(tmp_path / "agents.db"))
    lifecycle = ModelingAgentRunService(store, agent_store)

    task, run = lifecycle.start(
        project["project_id"],
        "problem_parsing",
        "modeling",
        "modeling_problem_parser",
        {"artifact_id": "input-1"},
        ["problem/problem_spec.json"],
    )
    lifecycle.complete(task["task_id"], run["run_id"], ["artifact-1"])

    [loaded_task] = store.list_tasks(project["project_id"])
    loaded_run = agent_store.get_agent_run(run["run_id"])
    assert loaded_task["status"] == "completed"
    assert loaded_run["status"] == "completed"
    assert loaded_run["project_id"] == project["project_id"]
    assert loaded_run["task_id"] == task["task_id"]
    assert loaded_run["steps"][0]["payload"]["artifact_ids"] == ["artifact-1"]


def test_third_failure_blocks_same_modeling_task(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(tmp_path / "workspace"), None)
    agent_store = DocumentMetadataStore(str(tmp_path / "agents.db"))
    lifecycle = ModelingAgentRunService(store, agent_store)
    task, run = lifecycle.start(
        project["project_id"],
        "model_planning",
        "modeling",
        "modeling_planner",
        {},
        ["analysis/model_plan.json"],
    )

    lifecycle.fail(task, run["run_id"], "invalid output")
    lifecycle.fail(task, run["run_id"], "invalid output")
    lifecycle.fail(task, run["run_id"], "invalid output")

    [loaded_task] = store.list_tasks(project["project_id"])
    assert loaded_task["retry_count"] == 3
    assert loaded_task["status"] == "blocked"
    assert agent_store.get_agent_run(run["run_id"])["status"] == "failed"


def test_run_creation_failure_compensates_task_state(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(tmp_path / "workspace"), None)

    class FailingAgentStore:
        def create_agent_run(self, *args, **kwargs):
            raise RuntimeError("agent database unavailable")

    lifecycle = ModelingAgentRunService(store, FailingAgentStore())
    with pytest.raises(RuntimeError, match="agent database unavailable"):
        lifecycle.start(
            project["project_id"],
            "problem_parsing",
            "modeling",
            "modeling_problem_parser",
            {},
            ["problem/problem_spec.json"],
        )

    [task] = store.list_tasks(project["project_id"])
    assert task["status"] == "failed"
    assert task["retry_count"] == 1


def test_failure_step_error_still_updates_run_and_task(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(tmp_path / "workspace"), None)
    delegate = DocumentMetadataStore(str(tmp_path / "agents.db"))

    class StepFailingAgentStore:
        def create_agent_run(self, *args, **kwargs):
            return delegate.create_agent_run(*args, **kwargs)

        def append_agent_step(self, *args, **kwargs):
            raise RuntimeError("step store unavailable")

        def update_agent_run_status(self, *args, **kwargs):
            return delegate.update_agent_run_status(*args, **kwargs)

    lifecycle = ModelingAgentRunService(store, StepFailingAgentStore())
    task, run = lifecycle.start(
        project["project_id"],
        "problem_parsing",
        "modeling",
        "modeling_problem_parser",
        {},
        ["problem/problem_spec.json"],
    )
    lifecycle.fail(task, run["run_id"], "safe failure")

    assert store.get_task(task["task_id"])["status"] == "failed"
    assert delegate.get_agent_run(run["run_id"])["status"] == "failed"


def test_failure_status_update_retries_without_leaking_store_error(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(tmp_path / "workspace"), None)
    delegate = DocumentMetadataStore(str(tmp_path / "agents.db"))

    class FlakyStatusAgentStore:
        def __init__(self):
            self.status_calls = 0

        def create_agent_run(self, *args, **kwargs):
            return delegate.create_agent_run(*args, **kwargs)

        def append_agent_step(self, *args, **kwargs):
            return delegate.append_agent_step(*args, **kwargs)

        def update_agent_run_status(self, *args, **kwargs):
            self.status_calls += 1
            if self.status_calls == 1:
                raise RuntimeError("C:\\private\\agents.db unavailable")
            return delegate.update_agent_run_status(*args, **kwargs)

    agent_store = FlakyStatusAgentStore()
    lifecycle = ModelingAgentRunService(store, agent_store)
    task, run = lifecycle.start(
        project["project_id"],
        "problem_parsing",
        "modeling",
        "modeling_problem_parser",
        {},
        ["problem/problem_spec.json"],
    )

    lifecycle.fail(task, run["run_id"], "safe failure")

    assert agent_store.status_calls == 2
    assert store.get_task(task["task_id"])["status"] == "failed"
    assert delegate.get_agent_run(run["run_id"])["status"] == "failed"
    assert delegate.get_agent_run(run["run_id"])["error"] == "safe failure"
