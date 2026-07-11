import subprocess

import pytest

from services.approval_service import ApprovalService
from services.git_commit_service import GitCommitService


class FakePolicy:
    def review(self, project, paths):
        return {"ok": True, "paths": sorted(paths), "issues": [], "diff": "diff"}

    def file_hashes(self, project, paths):
        return {path: "a" * 64 for path in sorted(paths)}


class FakeGit:
    def __init__(self):
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append(command)
        if command[1:4] == ["diff", "--cached", "--quiet"]:
            return subprocess.CompletedProcess(command, 1, "", "")
        if command[1:] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "abc123\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")


class PassingReproducibility:
    def check(self, project_id):
        return {"ok": True}


class FailingReproducibility:
    def check(self, project_id):
        return {"ok": False}


def test_commit_adds_only_approved_paths(tmp_path):
    project, store, service, fake_git = _service(tmp_path)
    request = service.request_commit(project["project_id"], ["README.md", "deliverables/manifest.json"], "feat: add modeling solution")
    ApprovalService(store).decide(request["approval_id"], "approved", request["payload_hash"])

    result = service.commit(project["project_id"], ["README.md", "deliverables/manifest.json"], "feat: add modeling solution")

    assert fake_git.commands[0] == ["git", "add", "--", "README.md", "deliverables/manifest.json"]
    assert result["commit_hash"] == "abc123"


def test_commit_rejects_changed_message(tmp_path):
    project, store, service, _ = _service(tmp_path)
    request = service.request_commit(project["project_id"], ["README.md"], "feat: add modeling solution")
    ApprovalService(store).decide(request["approval_id"], "approved", request["payload_hash"])

    with pytest.raises(ValueError, match="approval"):
        service.commit(project["project_id"], ["README.md"], "different message")


def test_request_commit_requires_passing_reproducibility_check(tmp_path):
    project, _, service, _ = _service(tmp_path, reproducibility=FailingReproducibility())

    with pytest.raises(ValueError, match="Reproducibility"):
        service.request_commit(project["project_id"], ["README.md"], "feat: add modeling solution")


def _service(tmp_path, reproducibility=None):
    from services.modeling_store import ModelingStore

    root = tmp_path / "project"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "README.md").write_text("# Solution", encoding="utf-8")
    (root / "deliverables").mkdir()
    (root / "deliverables/manifest.json").write_text("{}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "db.sqlite"))
    project = store.create_project("Forecast", "forecast", str(root), None)
    store.create_artifact(
        project["project_id"], "delivery_manifest", "deliverables/manifest.json", "b" * 64,
        None, None, 1,
    )
    fake_git = FakeGit()
    return project, store, GitCommitService(store, ApprovalService(store), FakePolicy(), reproducibility=reproducibility or PassingReproducibility(), git_run=fake_git), fake_git
