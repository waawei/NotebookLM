import hashlib
from pathlib import Path

import pytest

from services.git_policy_service import GitPolicyService


def test_policy_rejects_secret_and_large_file(tmp_path):
    project = _git_project(tmp_path)
    (project / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (project / "large.bin").write_bytes(b"x" * (20 * 1024 * 1024 + 1))

    review = GitPolicyService().review({"workspace_path": str(project)}, [".env", "large.bin"])

    assert review["ok"] is False
    assert {issue["code"] for issue in review["issues"]} == {"forbidden_path", "file_too_large"}


def test_policy_rejects_project_external_symlink(tmp_path):
    project = _git_project(tmp_path)
    external = tmp_path / "secret.txt"
    external.write_text("secret", encoding="utf-8")
    link = project / "linked.txt"
    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip("symlink creation is unavailable on this Windows host")

    review = GitPolicyService().review({"workspace_path": str(project)}, ["linked.txt"])

    assert review["ok"] is False
    assert {issue["code"] for issue in review["issues"]} == {"external_symlink"}


def test_policy_returns_reviewable_diff_for_untracked_text(tmp_path):
    project = _git_project(tmp_path)
    (project / "README.md").write_text("# Solution\n", encoding="utf-8")

    review = GitPolicyService().review({"workspace_path": str(project)}, ["README.md"])

    assert review["ok"] is True
    assert review["paths"] == ["README.md"]
    assert "+# Solution" in review["diff"]
    assert review["diff_hash"] == hashlib.sha256(review["diff"].encode("utf-8")).hexdigest()


def _git_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    return project
