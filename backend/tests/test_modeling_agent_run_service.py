from services.document_metadata_store import DocumentMetadataStore
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_store import ModelingStore


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
