import json
import zipfile
from pathlib import Path

from services.artifact_service import ArtifactService
from services.delivery_service import DeliveryService
from services.modeling_store import ModelingStore


def test_archive_contains_code_not_raw_data_and_registers_manifest(tmp_path):
    workspace = _workspace(tmp_path)
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    for artifact_type, relative_path in [
        ("paper_pdf", "deliverables/paper.pdf"),
        ("paper_markdown", "paper/draft.md"),
        ("paper_latex", "paper/main.tex"),
    ]:
        artifacts.register(project["project_id"], artifact_type, relative_path)
    for experiment_id in ("exp-0001", "exp-0002"):
        store.create_experiment(experiment_id, project["project_id"], _config(experiment_id), "a" * 64)
        store.update_experiment_status(experiment_id, "completed")

    result = DeliveryService(store, artifacts).build(project["project_id"])

    with zipfile.ZipFile(workspace / "deliverables/code.zip") as archive:
        names = set(archive.namelist())
    manifest = json.loads((workspace / "deliverables/manifest.json").read_text(encoding="utf-8"))
    assert "src/train.py" in names
    assert "requirements.txt" in names
    assert not any(name.startswith("data/raw/") for name in names)
    assert result["manifest_artifact"]["artifact_type"] == "delivery_manifest"
    raw_data = next(item for item in manifest["files"] if item["relative_path"] == "data/raw/source.csv")
    assert raw_data["included_in_git"] is False
    assert raw_data["exclusion_reason"] == "restricted_raw_data"


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
    (workspace / "data/data_manifest.json").write_text(json.dumps([{"relative_path": "data/raw/source.csv", "sha256": "ignored"}]), encoding="utf-8")
    for experiment_id in ("exp-0001", "exp-0002"):
        directory = workspace / "experiments" / experiment_id
        directory.mkdir(parents=True)
        for name, content in {"config.json": "{}", "metrics.json": "[]", "environment.json": "{}", "run.log": "ok"}.items():
            (directory / name).write_text(content, encoding="utf-8")
    return workspace


def _config(experiment_id: str) -> dict:
    return {"experiment_id": experiment_id, "seed": 42, "target": "sales", "features": ["price"], "model": {"kind": "baseline", "parameters": {}}, "metrics": [{"name": "rmse", "direction": "minimize"}]}
