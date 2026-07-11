from pathlib import Path

from services.artifact_service import ArtifactService
from services.modeling_store import ModelingStore
from services.reproducibility_service import ReproducibilityService


def test_check_requires_pdf_code_dependencies_and_completed_experiments(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)

    result = ReproducibilityService(store).check(project["project_id"])

    assert result["ok"] is False
    assert {item["code"] for item in result["issues"]} >= {
        "missing_pdf",
        "missing_reproduce_command",
        "missing_completed_experiments",
    }


def test_check_detects_artifact_hash_mismatch(tmp_path):
    workspace = tmp_path / "workspace"
    artifact_path = workspace / "paper" / "draft.md"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text("original", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifact_path.write_text("changed", encoding="utf-8")

    result = ReproducibilityService(store).check(project["project_id"])

    assert "artifact_hash_mismatch" in {item["code"] for item in result["issues"]}


def test_check_detects_current_delivery_manifest_hash_mismatch(tmp_path):
    workspace = tmp_path / "workspace"
    artifact_path = workspace / "deliverables" / "manifest.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text("original", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "delivery_manifest", "deliverables/manifest.json")
    artifact_path.write_text("changed", encoding="utf-8")

    result = ReproducibilityService(store).check(project["project_id"])

    assert "artifact_hash_mismatch" in {item["code"] for item in result["issues"]}


def test_check_accepts_complete_registered_delivery_inputs(tmp_path):
    workspace = tmp_path / "workspace"
    _write_complete_workspace(workspace)
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    for artifact_type, relative_path, experiment_id in [
        ("paper_pdf", "deliverables/paper.pdf", None),
        ("paper_markdown", "paper/draft.md", None),
        ("paper_latex", "paper/main.tex", None),
        ("paper_claim_target", "experiments/exp-0001/figure.png", "exp-0001"),
    ]:
        artifacts.register(project["project_id"], artifact_type, relative_path, source_experiment_id=experiment_id)
    for experiment_id in ("exp-0001", "exp-0002"):
        store.create_experiment(experiment_id, project["project_id"], _experiment_config(experiment_id), "a" * 64)
        store.update_experiment_status(experiment_id, "completed")

    result = ReproducibilityService(store).check(project["project_id"])

    assert result == {"ok": True, "issues": []}


def _write_complete_workspace(workspace: Path) -> None:
    (workspace / "deliverables").mkdir(parents=True)
    (workspace / "paper").mkdir()
    (workspace / "src").mkdir()
    (workspace / "data").mkdir()
    (workspace / "deliverables" / "paper.pdf").write_bytes(b"pdf")
    (workspace / "paper" / "draft.md").write_text("# Paper", encoding="utf-8")
    (workspace / "paper" / "main.tex").write_text("\\documentclass{article}", encoding="utf-8")
    (workspace / "requirements.txt").write_text("numpy==1.0", encoding="utf-8")
    (workspace / "reproduce.ps1").write_text("python src/train.py", encoding="utf-8")
    (workspace / "src" / "train.py").write_text("print('ok')", encoding="utf-8")
    (workspace / "data" / "data_manifest.json").write_text("[]", encoding="utf-8")
    for experiment_id in ("exp-0001", "exp-0002"):
        directory = workspace / "experiments" / experiment_id
        directory.mkdir(parents=True)
        (directory / "config.json").write_text("{}", encoding="utf-8")
        (directory / "metrics.json").write_text("[]", encoding="utf-8")
        (directory / "environment.json").write_text("{}", encoding="utf-8")
        (directory / "run.log").write_text("ok", encoding="utf-8")
    (workspace / "experiments" / "exp-0001" / "figure.png").write_bytes(b"figure")


def _experiment_config(experiment_id: str) -> dict:
    return {
        "experiment_id": experiment_id,
        "seed": 42,
        "target": "sales",
        "features": ["price"],
        "model": {"kind": "baseline", "parameters": {}},
        "metrics": [{"name": "rmse", "direction": "minimize"}],
    }
