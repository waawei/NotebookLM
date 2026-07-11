import json
import subprocess
from pathlib import Path

import pytest

from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.delivery_service import DeliveryService
from services.git_commit_service import GitCommitService
from services.git_policy_service import GitPolicyService
from services.modeling_store import ModelingStore


def test_phase5_packages_scans_invalidates_and_commits_without_remote(tmp_path):
    workspace = _workspace(tmp_path)
    _git(workspace, "init")
    _git(workspace, "config", "user.email", "checkpoint@example.test")
    _git(workspace, "config", "user.name", "Checkpoint")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    for artifact_type, relative_path in [("paper_pdf", "deliverables/paper.pdf"), ("paper_markdown", "paper/draft.md"), ("paper_latex", "paper/main.tex")]:
        artifacts.register(project["project_id"], artifact_type, relative_path)
    for experiment_id in ("exp-0001", "exp-0002"):
        store.create_experiment(experiment_id, project["project_id"], _config(experiment_id), "a" * 64)
        store.update_experiment_status(experiment_id, "completed")
    delivery = DeliveryService(store, artifacts)
    built = delivery.build(project["project_id"])
    policy = GitPolicyService()
    (workspace / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (workspace / "large.bin").write_bytes(b"x" * (20 * 1024 * 1024 + 1))
    blocked = policy.review(project, [".env", "large.bin"])
    assert {issue["code"] for issue in blocked["issues"]} == {"forbidden_path", "file_too_large"}
    (workspace / ".env").unlink()
    (workspace / "large.bin").unlink()
    (workspace / "README.md").write_text("# Solution\n", encoding="utf-8")
    paths = ["README.md", "deliverables/code.zip", "deliverables/manifest.json"]
    service = GitCommitService(store, ApprovalService(store), policy, delivery.reproducibility)
    request = service.request_commit(project["project_id"], paths, "feat: add modeling solution")
    ApprovalService(store).decide(request["approval_id"], "approved", request["payload_hash"])
    (workspace / "README.md").write_text("# Changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="approval"):
        service.commit(project["project_id"], paths, "feat: add modeling solution")
    request = service.request_commit(project["project_id"], paths, "feat: add modeling solution")
    ApprovalService(store).decide(request["approval_id"], "approved", request["payload_hash"])
    commit = service.commit(project["project_id"], paths, "feat: add modeling solution")

    manifest = json.loads((workspace / "deliverables/manifest.json").read_text(encoding="utf-8"))
    assert built["manifest_artifact"]["artifact_type"] == "delivery_manifest"
    assert (workspace / "deliverables/code.zip").is_file()
    assert any(item["relative_path"] == "data/raw/source.csv" and item["exclusion_reason"] == "restricted_raw_data" for item in manifest["files"])
    assert _git(workspace, "log", "-1", "--pretty=%s").stdout.strip() == "feat: add modeling solution"
    assert commit["commit_hash"] == _git(workspace, "rev-parse", "HEAD").stdout.strip()
    assert _git(workspace, "remote").stdout == ""


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    for directory in ("deliverables", "paper", "src", "data/raw"):
        (workspace / directory).mkdir(parents=True, exist_ok=True)
    (workspace / "deliverables/paper.pdf").write_bytes(b"pdf")
    (workspace / "paper/draft.md").write_text("# Paper", encoding="utf-8")
    (workspace / "paper/main.tex").write_text("\\documentclass{article}", encoding="utf-8")
    (workspace / "src/train.py").write_text("print('ok')", encoding="utf-8")
    (workspace / "requirements.txt").write_text("numpy==1.0", encoding="utf-8")
    (workspace / "reproduce.ps1").write_text("python src/train.py", encoding="utf-8")
    (workspace / "data/raw/source.csv").write_text("value\n1\n", encoding="utf-8")
    (workspace / "data/data_manifest.json").write_text(json.dumps({"files": [{"relative_path": "data/raw/source.csv", "sha256": "ignored"}]}), encoding="utf-8")
    for experiment_id in ("exp-0001", "exp-0002"):
        directory = workspace / "experiments" / experiment_id
        directory.mkdir(parents=True)
        for name, content in {"config.json": "{}", "metrics.json": "[]", "environment.json": "{}", "run.log": "ok"}.items():
            (directory / name).write_text(content, encoding="utf-8")
    return workspace


def _config(experiment_id: str) -> dict:
    return {"experiment_id": experiment_id, "seed": 42, "target": "sales", "features": ["price"], "model": {"kind": "baseline", "parameters": {}}, "metrics": [{"name": "rmse", "direction": "minimize"}]}


def _git(workspace: Path, *arguments: str):
    return subprocess.run(["git", *arguments], cwd=workspace, capture_output=True, text=True, check=True)
