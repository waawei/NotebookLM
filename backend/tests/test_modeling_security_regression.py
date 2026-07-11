import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from services.git_policy_service import GitPolicyService, resolve_git_path
from services.restricted_runner import RestrictedRunner
from services.modeling_input_service import ModelingInputService
from services.modeling_store import ModelingStore
from services.artifact_service import ArtifactService
from services.approval_service import ApprovalService
from services.git_commit_service import GitCommitService
from test_git_commit_service import FakeGit, FakePolicy, PassingReproducibility, _service


@pytest.mark.parametrize(
    "relative", ["../escape.txt", "C:/Windows/win.ini", "/etc/passwd", "data/raw/../../secret"]
)
def test_git_paths_reject_escapes(relative, tmp_path):
    with pytest.raises(ValueError):
        resolve_git_path(tmp_path, relative)


@pytest.mark.parametrize("filename", ["../escape.csv", "C:/Windows/win.ini", "/etc/passwd", "data/raw/../../secret.csv"])
def test_input_service_rejects_escape_names(filename, tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "data" / "raw").mkdir(parents=True)
    (workspace / "problem" / "original").mkdir(parents=True)
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    service = ModelingInputService(store, ArtifactService(store), 1024)

    with pytest.raises(ValueError, match="Invalid input filename"):
        service.import_input(project["project_id"], filename, b"x\n1\n", "data")


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


def test_runner_kills_child_processes_after_timeout(tmp_path):
    result = RestrictedRunner().run(
        [sys.executable, "-c", "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); time.sleep(30)"],
        tmp_path, 1, 4096, True,
    )
    assert result.timed_out is True
    time.sleep(0.2)
    assert all(process.info["cmdline"] is None or "time.sleep(30)" not in " ".join(process.info["cmdline"]) for process in __import__("psutil").process_iter(["cmdline"]))


def test_git_policy_blocks_symlinks_forbidden_paths_secrets_and_large_files(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (project / "settings.py").write_text("API_KEY=secret", encoding="utf-8")
    (project / "large.bin").write_bytes(b"x" * (20 * 1024 * 1024 + 1))
    review = GitPolicyService().review(
        {"workspace_path": str(project)}, [".env", "settings.py", "large.bin"]
    )
    assert review["ok"] is False
    assert {item["code"] for item in review["issues"]} == {
        "forbidden_path", "secret_detected", "file_too_large"
    }


def test_git_policy_blocks_external_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    external = tmp_path / "outside.txt"
    external.write_text("outside", encoding="utf-8")
    link = project / "linked.txt"
    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip("symlink creation is unavailable on this Windows host")

    review = GitPolicyService().review({"workspace_path": str(project)}, ["linked.txt"])
    assert review["ok"] is False
    assert review["issues"][0]["code"] == "external_symlink"


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


def test_commit_rejects_empty_staging_and_stale_approval(tmp_path):
    project, store, service, fake_git = _service(tmp_path)
    request = service.request_commit(project["project_id"], ["README.md"], "feat: add modeling solution")
    ApprovalService(store).decide(request["approval_id"], "approved", request["payload_hash"])
    class EmptyGit(FakeGit):
        def __init__(self):
            super().__init__()
            self.added = False

        def __call__(self, command, **kwargs):
            self.commands.append(command)
            if command[1:3] == ["add", "--"]:
                self.added = True
                return subprocess.CompletedProcess(command, 0, "", "")
            if command[1:4] == ["diff", "--cached", "--name-only"]:
                return subprocess.CompletedProcess(command, 0, "README.md\n" if self.added else "", "")
            if command[1:4] == ["diff", "--cached", "--quiet"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            return super().__call__(command, **kwargs)

    service.git_run = EmptyGit()

    with pytest.raises(ValueError, match="No approved changes"):
        service.commit(project["project_id"], ["README.md"], "feat: add modeling solution")
    with pytest.raises(ValueError, match="approval"):
        service.commit(project["project_id"], ["README.md"], "different message")


def test_git_commit_flow_never_invokes_forbidden_commands(tmp_path):
    project, store, service, fake_git = _service(tmp_path)
    request = service.request_commit(project["project_id"], ["README.md"], "feat: add modeling solution")
    ApprovalService(store).decide(request["approval_id"], "approved", request["payload_hash"])
    service.commit(project["project_id"], ["README.md"], "feat: add modeling solution")

    forbidden = {"push", "reset", "clean", "rebase", "remote", "checkout"}
    assert all(not forbidden.intersection(command) for command in fake_git.commands)
