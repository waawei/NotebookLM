import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from api import modeling


class FakeProjectService:
    def __init__(self, state="project_initialized"):
        self.project = {
            "project_id": "p-1",
            "state": state,
            "workspace_path": "D:/projects/p-1",
        }

    def get_project(self, project_id):
        return self.project if project_id == "p-1" else None


class FakeInputService:
    def __init__(self):
        self.calls = []

    def import_input(self, project_id, filename, content, kind):
        self.calls.append((project_id, filename, content, kind))
        return {"artifact_id": "input-1", "artifact_type": f"{kind}_input"}


class FakeApprovalService:
    def __init__(self):
        self.calls = []

    def decide(self, approval_id, decision, payload_hash, comment=""):
        self.calls.append((approval_id, decision, payload_hash, comment))
        return {"approval_id": approval_id, "decision": decision}

    def decide_for_project(
        self, project_id, approval_id, decision, payload_hash, comment=""
    ):
        if project_id != "p-1":
            raise ValueError("Approval request not found")
        return self.decide(approval_id, decision, payload_hash, comment)

    def list_for_project(self, project_id):
        return [{"approval_id": "a-1", "project_id": project_id}]


@pytest.fixture
def fake_services(monkeypatch):
    projects = FakeProjectService()
    inputs = FakeInputService()
    approvals = FakeApprovalService()
    monkeypatch.setattr(modeling, "project_service", projects)
    monkeypatch.setattr(modeling, "input_service", inputs, raising=False)
    monkeypatch.setattr(modeling, "approval_service", approvals)
    return projects, inputs, approvals


def test_upload_rejects_unknown_kind():
    request = modeling.InputUploadKind(kind="executable")
    with pytest.raises(HTTPException) as raised:
        asyncio.run(modeling.validate_input_kind(request))
    assert raised.value.status_code == 400


def test_upload_reads_bytes_and_preserves_filename(fake_services):
    _, inputs, _ = fake_services
    upload = UploadFile(filename="赛题.txt", file=BytesIO("预测销量".encode("utf-8")))

    response = asyncio.run(modeling.upload_input("p-1", upload, "problem"))

    assert response["artifact_type"] == "problem_input"
    assert inputs.calls == [
        ("p-1", "赛题.txt", "预测销量".encode("utf-8"), "problem")
    ]


def test_approval_decision_passes_payload_hash(fake_services):
    _, _, approvals = fake_services
    response = asyncio.run(
        modeling.decide_approval(
            "p-1",
            "a-1",
            modeling.ApprovalDecision(
                decision="approved", payload_hash="abc", comment="ok"
            ),
        )
    )

    assert response["decision"] == "approved"
    assert approvals.calls == [("a-1", "approved", "abc", "ok")]


def test_invalid_state_and_stale_approval_return_conflict(fake_services):
    projects, _, approvals = fake_services
    projects.project["state"] = "project_initialized"
    with pytest.raises(HTTPException) as state_error:
        asyncio.run(modeling.parse_problem("p-1"))
    assert state_error.value.status_code == 409

    def stale(*args, **kwargs):
        raise ValueError("Approval payload has changed")

    approvals.decide = stale
    with pytest.raises(HTTPException) as approval_error:
        asyncio.run(
            modeling.decide_approval(
                "p-1",
                "a-1",
                modeling.ApprovalDecision(
                    decision="approved", payload_hash="stale", comment=""
                ),
            )
        )
    assert approval_error.value.status_code == 409


def test_phase2_routes_are_registered():
    paths = {route.path for route in modeling.router.routes}
    assert "/projects/{project_id}/inputs" in paths
    assert "/projects/{project_id}/problem/parse" in paths
    assert "/projects/{project_id}/data/profile/{artifact_id}" in paths
    assert "/projects/{project_id}/model-plan" in paths
    assert "/projects/{project_id}/artifacts" in paths
    assert "/projects/{project_id}/approvals/{approval_id}/decide" in paths


def test_upload_rejects_oversized_body_before_input_service(fake_services, monkeypatch):
    _, inputs, _ = fake_services
    monkeypatch.setattr(modeling.settings, "MAX_FILE_SIZE", 4)
    upload = UploadFile(filename="large.csv", file=BytesIO(b"12345"))

    with pytest.raises(HTTPException) as raised:
        asyncio.run(modeling.upload_input("p-1", upload, "data"))

    assert raised.value.status_code == 400
    assert inputs.calls == []
    assert upload.file.closed


def test_upload_is_rejected_after_project_initialization(fake_services):
    projects, inputs, _ = fake_services
    projects.project["state"] = "problem_parsing"
    upload = UploadFile(filename="train.csv", file=BytesIO(b"x\n1\n"))

    with pytest.raises(HTTPException) as raised:
        asyncio.run(modeling.upload_input("p-1", upload, "data"))

    assert raised.value.status_code == 409
    assert inputs.calls == []


def test_approval_decision_rejects_cross_project_request(monkeypatch, tmp_path):
    from services.approval_service import ApprovalService
    from services.modeling_store import ModelingStore

    store = ModelingStore(str(tmp_path / "modeling.db"))
    project_a = store.create_project("A", "a", str(tmp_path / "a"), None)
    project_b = store.create_project("B", "b", str(tmp_path / "b"), None)
    approvals = ApprovalService(store)
    request = approvals.request(project_b["project_id"], "model_approval", {"version": 1})

    class Projects:
        def get_project(self, project_id):
            return store.get_project(project_id)

    monkeypatch.setattr(modeling, "project_service", Projects())
    monkeypatch.setattr(modeling, "approval_service", approvals)
    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            modeling.decide_approval(
                project_a["project_id"],
                request["approval_id"],
                modeling.ApprovalDecision(
                    decision="approved",
                    payload_hash=request["payload_hash"],
                    comment="",
                ),
            )
        )

    assert raised.value.status_code == 409
    assert store.get_approval_request(request["approval_id"])["status"] == "pending"
