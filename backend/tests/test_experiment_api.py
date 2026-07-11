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
