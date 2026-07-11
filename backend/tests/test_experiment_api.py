import asyncio
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from api import modeling


def test_result_gate_requires_baseline_candidate_and_metrics(tmp_path):
    from services.approval_service import ApprovalService
    from services.modeling_gate_service import ModelingGateService
    from services.modeling_store import ModelingStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    gate = ModelingGateService(store, ApprovalService(store))

    with pytest.raises(ValueError, match="completed baseline and candidate"):
        gate.require_exit(project["project_id"], "result_validation")


def test_result_gate_rejects_two_baselines_and_invalid_validation_metric(tmp_path):
    from services.approval_service import ApprovalService
    from services.modeling_gate_service import ModelingGateService
    from services.modeling_store import ModelingStore

    workspace = tmp_path / "workspace"
    (workspace / "experiments" / "exp-0001").mkdir(parents=True)
    (workspace / "experiments" / "exp-0002").mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    config = {"seed": 42, "target": "sales", "features": ["price"], "metrics": [{"name": "rmse", "direction": "minimize"}]}
    for experiment_id in ("exp-0001", "exp-0002"):
        item = {**config, "experiment_id": experiment_id, "model": {"kind": "baseline", "parameters": {}}}
        store.create_experiment(experiment_id, project["project_id"], item, None)
        store.update_experiment_status(experiment_id, "completed")
        (workspace / "experiments" / experiment_id / "metrics.json").write_text('[{"split":"validation"}]', encoding="utf-8")
    gate = ModelingGateService(store, ApprovalService(store))

    with pytest.raises(ValueError, match="completed baseline and candidate"):
        gate.require_exit(project["project_id"], "result_validation")


def test_execute_returns_conflict_for_stale_approval(monkeypatch):
    project_service = Mock()
    project_service.get_project.return_value = {
        "project_id": "p-1", "state": "execution_approval_pending", "workspace_path": "D:/projects/p-1"
    }
    experiment_service = Mock()
    experiment_service.execute.side_effect = ValueError("Required approval does not match current content")
    monkeypatch.setattr(modeling, "project_service", project_service)
    monkeypatch.setattr(modeling, "experiment_service", experiment_service, raising=False)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(modeling.execute_experiment("p-1", "exp-0001"))

    assert raised.value.status_code == 409
