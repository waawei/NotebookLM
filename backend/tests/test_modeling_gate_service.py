import hashlib

import pytest

from services.approval_service import ApprovalService, canonical_hash
from services.artifact_service import ArtifactService
from services.modeling_gate_service import ModelingGateService
from services.modeling_project_service import ModelingProjectService
from services.modeling_store import ModelingStore


def test_gate_requires_artifacts_for_current_state(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    gate = ModelingGateService(store, ApprovalService(store))

    with pytest.raises(ValueError, match="problem_spec"):
        gate.require_exit(project["project_id"], "problem_parsing")


def test_gate_requires_matching_model_approval_and_rejects_modified_plan(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "analysis").mkdir(parents=True)
    plan_path = workspace / "analysis" / "model_plan.json"
    plan_path.write_text('{"candidates": []}\n', encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    store.update_state(project["project_id"], "model_approval_pending")
    artifact = ArtifactService(store).register(
        project["project_id"], "model_plan", "analysis/model_plan.json"
    )
    approvals = ApprovalService(store)
    payload = {
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": artifact["sha256"],
        "version": artifact["version"],
    }
    request = approvals.request(project["project_id"], "model_approval", payload)
    approvals.decide(request["approval_id"], "approved", request["payload_hash"])
    gate = ModelingGateService(store, approvals)
    service = ModelingProjectService(store, None, gate_service=gate)

    advanced = service.advance(project["project_id"])
    assert advanced["state"] == "experiment_implementation"

    store.update_state(project["project_id"], "model_approval_pending")
    plan_path.chmod(0o666)
    plan_path.write_text('{"candidates": [{"changed": true}]}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="approval"):
        service.advance(project["project_id"])
    assert store.get_project(project["project_id"])["state"] == "model_approval_pending"
    assert hashlib.sha256(plan_path.read_bytes()).hexdigest() != artifact["sha256"]
    assert canonical_hash(payload) == request["payload_hash"]
