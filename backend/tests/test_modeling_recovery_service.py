import asyncio
from pathlib import Path

from fastapi import HTTPException

from api import modeling
from services.document_metadata_store import DocumentMetadataStore
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_store import ModelingStore


def _config(experiment_id: str = "exp-0001") -> dict:
    return {
        "experiment_id": experiment_id,
        "seed": 42,
        "target": "sales",
        "features": ["price"],
        "model": {"kind": "baseline", "parameters": {}},
        "metrics": [{"name": "rmse", "direction": "minimize"}],
    }


def test_recovery_marks_running_experiment_interrupted_and_returns_safe_state(tmp_path):
    from services.modeling_recovery_service import ModelingRecoveryService

    workspace = tmp_path / "project"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    store.update_state(project["project_id"], "experiment_running")
    store.create_experiment("exp-0001", project["project_id"], _config(), None)
    store.update_experiment_status("exp-0001", "running")

    result = ModelingRecoveryService(store).recover_interrupted_projects()

    assert result == [{
        "project_id": project["project_id"],
        "recovered_from": "experiment_running",
        "recovered_to": "experiment_implementation",
    }]
    assert store.get_project(project["project_id"])["state"] == "experiment_implementation"
    experiment = store.get_experiment("exp-0001")
    assert experiment["status"] == "failed"
    assert experiment["error_code"] == "interrupted"
    [recovery] = store.list_recoveries()
    assert recovery["from_state"] == "experiment_running"
    assert recovery["to_state"] == "experiment_implementation"
    assert recovery["interrupted_run_ids"] == ["exp-0001"]
    assert store.list_transitions(project["project_id"])[-1]["reason"] == "interrupted"


def test_recovery_is_idempotent_even_without_a_child_run(tmp_path):
    from services.modeling_recovery_service import ModelingRecoveryService

    workspace = tmp_path / "project"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    store.update_state(project["project_id"], "committing")
    recovery = ModelingRecoveryService(store)

    first = recovery.recover_interrupted_projects()
    second = recovery.recover_interrupted_projects()

    assert len(first) == 1
    assert second == []
    assert store.get_project(project["project_id"])["state"] == "packaging"
    assert len(store.list_recoveries()) == 1


def test_recovery_interrupts_running_workflow_task_and_agent_run(tmp_path):
    from services.modeling_recovery_service import ModelingRecoveryService

    workspace = tmp_path / "project"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    store.update_state(project["project_id"], "problem_parsing")
    agent_store = DocumentMetadataStore(str(tmp_path / "agents.db"))
    task, run = ModelingAgentRunService(store, agent_store).start(
        project["project_id"],
        "problem_parsing",
        "modeling",
        "modeling_problem_parser",
        {},
        ["problem/problem_spec.json"],
    )

    result = ModelingRecoveryService(store, agent_store).recover_interrupted_projects()

    assert result[0]["recovered_to"] == "project_initialized"
    assert store.get_task(task["task_id"])["status"] == "failed"
    assert agent_store.get_agent_run(run["run_id"])["status"] == "failed"
    assert agent_store.get_agent_run(run["run_id"])["error"] == "interrupted"
    [recovery] = store.list_recoveries()
    assert run["run_id"] in recovery["interrupted_run_ids"]


def test_recovery_continues_when_owned_pid_exits_during_inspection(tmp_path, monkeypatch):
    from services.modeling_recovery_service import ModelingRecoveryService

    workspace = tmp_path / "project"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    store.update_state(project["project_id"], "experiment_running")
    store.create_experiment("exp-0001", project["project_id"], _config(), None)
    store.update_experiment_status("exp-0001", "running", pid=1234)

    monkeypatch.setattr("services.modeling_recovery_service.psutil.pid_exists", lambda pid: True)
    monkeypatch.setattr(
        "services.modeling_recovery_service.psutil.Process",
        lambda pid: (_ for _ in ()).throw(__import__("psutil").NoSuchProcess(pid)),
    )

    result = ModelingRecoveryService(store).recover_interrupted_projects()

    assert result[0]["recovered_to"] == "experiment_implementation"
    assert store.get_experiment("exp-0001")["error_code"] == "interrupted"


def test_recovery_refuses_to_stop_a_pid_outside_the_project_workspace(tmp_path, monkeypatch):
    from services.modeling_recovery_service import ModelingRecoveryService

    workspace = tmp_path / "project"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    store.update_state(project["project_id"], "experiment_running")
    store.create_experiment("exp-0001", project["project_id"], _config(), None)
    store.update_experiment_status("exp-0001", "running", pid=1234)

    class Process:
        def cmdline(self):
            return ["python", "outside.py"]

        def cwd(self):
            return str(tmp_path / "outside")

    monkeypatch.setattr("services.modeling_recovery_service.psutil.pid_exists", lambda pid: True)
    monkeypatch.setattr("services.modeling_recovery_service.psutil.Process", lambda pid: Process())

    try:
        ModelingRecoveryService(store).recover_interrupted_projects()
    except RuntimeError as error:
        assert str(error) == "Refusing to terminate a process not owned by this project"
    else:
        raise AssertionError("unowned process must not be terminated")

    assert store.get_project(project["project_id"])["state"] == "experiment_running"
    assert store.get_experiment("exp-0001")["status"] == "running"


def test_recovery_api_lists_undismissed_records_and_timestamps_dismissal(tmp_path, monkeypatch):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(tmp_path / "project"), None)
    recovery = store.create_recovery(
        project["project_id"], "committing", "packaging", []
    )
    monkeypatch.setattr(modeling, "modeling_store", store)

    assert asyncio.run(modeling.list_recoveries()) == {"recoveries": [recovery], "total": 1}
    dismissed = asyncio.run(modeling.dismiss_recovery(recovery["recovery_id"]))
    assert dismissed["dismissed_at"] is not None
    assert asyncio.run(modeling.list_recoveries()) == {"recoveries": [], "total": 0}

    try:
        asyncio.run(modeling.dismiss_recovery("missing"))
    except HTTPException as error:
        assert error.status_code == 404
    else:
        raise AssertionError("missing recovery must return 404")


def test_startup_reconciliation_logs_only_recovery_identifiers_and_states():
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")

    assert "recovery_service.recover_interrupted_projects()" in source
    assert "recovery['project_id']" in source
    assert "recovery['recovered_from']" in source
    assert "recovery['recovered_to']" in source
