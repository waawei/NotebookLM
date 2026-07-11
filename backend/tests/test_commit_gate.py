import pytest

from services.approval_service import ApprovalService
from services.modeling_gate_service import ModelingGateService
from services.modeling_store import ModelingStore


def test_packaging_gate_requires_manifest_and_reproducible_inputs(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "db.sqlite"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)

    with pytest.raises(ValueError, match="delivery manifest"):
        ModelingGateService(store, ApprovalService(store)).require_exit(project["project_id"], "packaging")


def test_committing_gate_requires_persisted_current_manifest_commit(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "db.sqlite"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    manifest = store.create_artifact(project["project_id"], "delivery_manifest", "deliverables/manifest.json", "a" * 64, None, None, 1)
    monkeypatch.setattr("services.modeling_gate_service.ReproducibilityService.check", lambda _self, _project_id: {"ok": True})

    with pytest.raises(ValueError, match="persisted approved commit"):
        ModelingGateService(store, ApprovalService(store)).require_exit(project["project_id"], "committing")

    store.create_project_commit(project["project_id"], "payload", "commit", "feat: delivery", manifest["sha256"])

    ModelingGateService(store, ApprovalService(store)).require_exit(project["project_id"], "committing")
