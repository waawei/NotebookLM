import hashlib
import json
import stat

import pytest

from services.artifact_service import ArtifactService
from services.modeling_input_service import ModelingInputService
from services.modeling_store import ModelingStore


@pytest.fixture
def input_context(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "problem" / "original").mkdir(parents=True)
    (workspace / "data" / "raw").mkdir(parents=True)
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    service = ModelingInputService(store, ArtifactService(store), max_file_size=64)
    return project, service, store, workspace


def test_imports_csv_with_hash_manifest_and_read_only_source(input_context):
    project, service, store, workspace = input_context
    content = b"x,y\n1,2\n"

    result = service.import_input(
        project["project_id"], "train.csv", content, "data"
    )

    target = workspace / "data" / "raw" / "train.csv"
    assert target.read_bytes() == content
    assert not target.stat().st_mode & stat.S_IWRITE
    assert result["artifact_type"] == "data_input"
    assert result["relative_path"] == "data/raw/train.csv"
    manifest = json.loads(
        (workspace / "data" / "data_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest == {
        "files": [
            {
                "filename": "train.csv",
                "relative_path": "data/raw/train.csv",
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        ]
    }
    assert store.list_artifacts(project["project_id"]) == [result]


def test_imports_utf8_problem_and_records_problem_manifest(input_context):
    project, service, _, workspace = input_context
    content = "预测未来销量，并说明约束。".encode("utf-8")

    result = service.import_input(
        project["project_id"], "赛题.txt", content, "problem"
    )

    assert result["artifact_type"] == "problem_input"
    assert (workspace / "problem" / "original" / "赛题.txt").read_bytes() == content
    manifest = json.loads(
        (workspace / "problem" / "input_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["files"][0]["sha256"] == hashlib.sha256(content).hexdigest()


@pytest.mark.parametrize(
    ("filename", "kind", "message"),
    [
        ("payload.py", "data", "Unsupported data file"),
        ("nested/train.csv", "data", "Invalid input filename"),
        ("train.csv", "executable", "Unsupported executable file"),
    ],
)
def test_rejects_unsupported_kinds_and_unsafe_names(
    input_context, filename, kind, message
):
    project, service, _, _ = input_context

    with pytest.raises(ValueError, match=message):
        service.import_input(project["project_id"], filename, b"x\n1\n", kind)


def test_rejects_duplicate_names_and_oversized_content(input_context):
    project, service, _, _ = input_context
    service.import_input(project["project_id"], "train.csv", b"x\n1\n", "data")

    with pytest.raises(ValueError, match="already exists"):
        service.import_input(project["project_id"], "train.csv", b"x\n2\n", "data")
    with pytest.raises(ValueError, match="size limit"):
        service.import_input(project["project_id"], "large.csv", b"x" * 65, "data")
