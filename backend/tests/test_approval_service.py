import hashlib

import pytest

from services.approval_service import ApprovalService, canonical_hash
from services.modeling_store import ModelingStore


@pytest.fixture
def project_store(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    return project, store


def test_changed_payload_invalidates_approval(project_store):
    project, store = project_store
    service = ApprovalService(store)
    request = service.request(
        project["project_id"],
        "model_approval",
        {"artifact_id": "a-1", "version": 1},
    )

    approved = service.decide(
        request["approval_id"],
        "approved",
        request["payload_hash"],
        "Looks correct",
    )

    assert approved["decision"] == "approved"
    assert service.require_approved(
        project["project_id"], "model_approval", request["payload_hash"]
    ) == approved
    with pytest.raises(ValueError, match="approval does not match"):
        service.require_approved(
            project["project_id"],
            "model_approval",
            hashlib.sha256(b"changed").hexdigest(),
        )


def test_approval_hash_is_canonical_and_decision_hash_must_match(project_store):
    project, store = project_store
    service = ApprovalService(store)
    payload = {"version": 1, "title": "预测", "nested": {"b": 2, "a": 1}}
    request = service.request(project["project_id"], "model_approval", payload)

    assert request["payload_hash"] == canonical_hash(
        {"nested": {"a": 1, "b": 2}, "title": "预测", "version": 1}
    )
    assert request["payload"] == payload
    with pytest.raises(ValueError, match="payload has changed"):
        service.decide(request["approval_id"], "approved", "stale")


def test_later_changes_request_revokes_an_earlier_approval(project_store):
    project, store = project_store
    service = ApprovalService(store)
    request = service.request(
        project["project_id"], "model_approval", {"artifact_id": "a-1"}
    )
    service.decide(request["approval_id"], "approved", request["payload_hash"])
    service.decide(
        request["approval_id"],
        "changes_requested",
        request["payload_hash"],
        "Revise assumptions",
    )

    with pytest.raises(ValueError, match="approval does not match"):
        service.require_approved(
            project["project_id"], "model_approval", request["payload_hash"]
        )
