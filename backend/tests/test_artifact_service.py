import hashlib

import pytest

from services.artifact_service import ArtifactService
from services.modeling_store import ModelingStore


@pytest.fixture
def project_store(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    return project, store, workspace


def test_artifact_registers_hash_and_rejects_escape(project_store, tmp_path):
    project, store, workspace = project_store
    target = workspace / "analysis" / "model_plan.md"
    target.parent.mkdir()
    target.write_text("plan", encoding="utf-8")

    service = ArtifactService(store)
    artifact = service.register(
        project["project_id"], "model_plan", "analysis/model_plan.md"
    )

    assert artifact["sha256"] == hashlib.sha256(b"plan").hexdigest()
    assert artifact["version"] == 1
    assert service.resolve(project["project_id"], artifact["artifact_id"]) == artifact
    assert service.list_for_project(project["project_id"]) == [artifact]

    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")
    with pytest.raises(ValueError, match="outside project workspace"):
        service.register(project["project_id"], "model_plan", "../secret.txt")


def test_artifact_registration_versions_changed_content(project_store):
    project, store, workspace = project_store
    target = workspace / "analysis" / "model_plan.md"
    target.parent.mkdir()
    target.write_text("first", encoding="utf-8")
    service = ArtifactService(store)

    first = service.register(
        project["project_id"], "model_plan", "analysis/model_plan.md"
    )
    target.write_text("second", encoding="utf-8")
    second = service.register(
        project["project_id"], "model_plan", "analysis/model_plan.md"
    )

    assert second["version"] == 2
    assert second["sha256"] != first["sha256"]
