import os
import subprocess
import sys
from pathlib import Path

import pytest

from services.git_policy_service import GitPolicyService, resolve_git_path
from services.restricted_runner import RestrictedRunner


@pytest.mark.parametrize(
    "relative", ["../escape.txt", "C:/Windows/win.ini", "/etc/passwd", "data/raw/../../secret"]
)
def test_git_paths_reject_escapes(relative, tmp_path):
    with pytest.raises(ValueError):
        resolve_git_path(tmp_path, relative)


@pytest.mark.parametrize("name", ["LLM_API_KEY", "AUTHORIZATION", "ACCESS_TOKEN", "DB_PASSWORD"])
def test_runner_never_forwards_sensitive_environment(name, monkeypatch, tmp_path):
    monkeypatch.setenv(name, "sensitive-value")
    result = RestrictedRunner().run(
        [sys.executable, "-c", f"import os; print(os.getenv('{name}'))"],
        tmp_path, 10, 4096, False,
    )
    assert "sensitive-value" not in result.stdout


def test_network_socket_is_denied(tmp_path):
    result = RestrictedRunner().run(
        [sys.executable, "-c", "import socket; socket.create_connection(('example.com', 80))"],
        tmp_path, 10, 4096, False,
    )
    assert result.exit_code != 0
    assert "Network access is disabled" in result.stderr


def test_runner_enforces_output_and_timeout_limits(tmp_path):
    output = RestrictedRunner().run(
        [sys.executable, "-c", "print('x' * (10 * 1024 * 1024 + 1))"],
        tmp_path, 10, 10 * 1024 * 1024, False,
    )
    timeout = RestrictedRunner().run(
        [sys.executable, "-c", "import time; time.sleep(5)"], tmp_path, 1, 4096, False,
    )
    assert output.error_code == "resource_error"
    assert len((output.stdout + output.stderr).encode()) <= 10 * 1024 * 1024
    assert timeout.error_code == "resource_error"
    assert timeout.timed_out is True


def test_git_policy_blocks_symlinks_forbidden_paths_secrets_and_large_files(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (project / "large.bin").write_bytes(b"x" * (20 * 1024 * 1024 + 1))
    external = tmp_path / "outside.txt"
    external.write_text("outside", encoding="utf-8")
    link = project / "linked.txt"
    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip("symlink creation is unavailable on this Windows host")

    review = GitPolicyService().review(
        {"workspace_path": str(project)}, [".env", "large.bin", "linked.txt"]
    )
    assert review["ok"] is False
    assert {item["code"] for item in review["issues"]} == {
        "forbidden_path", "file_too_large", "external_symlink"
    }


def test_git_policy_invokes_only_allowed_git_subcommands(monkeypatch, tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "README.md").write_text("# Solution\n", encoding="utf-8")
    commands = []

    class Result:
        returncode = 1
        stdout = ""

    def fake_run(command, **kwargs):
        commands.append(command)
        return Result()

    monkeypatch.setattr("services.git_policy_service.subprocess.run", fake_run)
    GitPolicyService().review({"workspace_path": str(project)}, ["README.md"])

    forbidden = {"push", "reset", "clean", "rebase", "remote", "checkout"}
    assert all(not forbidden.intersection(command) for command in commands)
