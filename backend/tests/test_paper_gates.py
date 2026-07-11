import pytest

from services.approval_service import ApprovalService
from services.modeling_gate_service import ModelingGateService
from services.modeling_store import ModelingStore


def test_final_gate_blocks_without_passing_review(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)

    with pytest.raises(ValueError, match="blocking review issues"):
        ModelingGateService(store, ApprovalService(store)).require_exit(project["project_id"], "final_approval_pending")


def test_final_gate_rejects_stale_review(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    store.create_review_run(project["project_id"], "old", [], "passed")

    with pytest.raises(ValueError, match="blocking review issues"):
        ModelingGateService(store, ApprovalService(store)).require_exit(project["project_id"], "final_approval_pending")
