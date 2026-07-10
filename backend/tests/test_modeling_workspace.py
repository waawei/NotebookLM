import subprocess

import pytest

from services.modeling_workspace import ModelingWorkspaceService


def test_workspace_rejects_source_tree_parent(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    service = ModelingWorkspaceService(str(source_root), str(source_root))

    with pytest.raises(ValueError, match="outside the application source tree"):
        service.create("forecast")


def test_workspace_creates_expected_project_skeleton_and_git_repo(tmp_path):
    source_root = tmp_path / "source"
    workspace_root = tmp_path / "projects"
    source_root.mkdir()
    service = ModelingWorkspaceService(str(workspace_root), str(source_root))

    path = service.create("forecast")

    assert path == workspace_root.resolve() / "forecast"
    assert (path / ".git").is_dir()
    for relative in (
        "problem/original",
        "data/raw",
        "analysis",
        "src",
        "tests",
        "experiments",
        "figures",
        "tables",
        "paper/sections",
        "deliverables",
        ".workflow/runs",
    ):
        assert (path / relative).is_dir()


def test_workspace_rejects_invalid_slug(tmp_path):
    service = ModelingWorkspaceService(str(tmp_path / "projects"), str(tmp_path / "source"))

    with pytest.raises(ValueError, match="Invalid project slug"):
        service.create("../forecast")


def test_workspace_cleans_up_when_git_init_fails(tmp_path, monkeypatch):
    service = ModelingWorkspaceService(str(tmp_path / "projects"), str(tmp_path / "source"))

    def fail_git_init(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["git", "init"], stderr="git missing")

    monkeypatch.setattr("services.modeling_workspace.subprocess.run", fail_git_init)

    with pytest.raises(subprocess.CalledProcessError):
        service.create("forecast")

    assert not (tmp_path / "projects" / "forecast").exists()
