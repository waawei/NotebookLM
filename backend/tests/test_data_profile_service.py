import json

import pytest

from services.artifact_service import ArtifactService
from services.data_profile_service import DataProfileService
from services.modeling_store import ModelingStore


@pytest.fixture
def profile_context(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "data" / "raw").mkdir(parents=True)
    (workspace / "analysis").mkdir()
    source = workspace / "data" / "raw" / "train.csv"
    source.write_text(
        "category,target\nA,1\nA,1\nB,\n",
        encoding="utf-8",
    )
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    data_artifact = artifacts.register(
        project["project_id"], "data_input", "data/raw/train.csv"
    )
    service = DataProfileService(store, artifacts)
    return project, data_artifact, service, store, workspace


def test_profiles_types_missing_duplicates_and_numeric_summary(profile_context):
    project, data_artifact, service, store, workspace = profile_context

    result = service.profile(project["project_id"], data_artifact["artifact_id"])

    assert result["row_count"] == 3
    assert result["column_count"] == 2
    assert result["duplicate_rows"] == 1
    assert result["columns"]["target"]["missing"] == 1
    assert result["columns"]["target"]["numeric"] == {
        "min": 1.0,
        "max": 1.0,
        "mean": 1.0,
        "std": 0.0,
    }
    persisted = json.loads(
        (workspace / "analysis" / "data_profile.json").read_text(encoding="utf-8")
    )
    assert persisted == result
    report = (workspace / "analysis" / "data_report.md").read_text(
        encoding="utf-8"
    )
    assert "Rows: 3" in report
    assert "Duplicate rows: 1" in report
    assert {item["artifact_type"] for item in store.list_artifacts(project["project_id"])} == {
        "data_input",
        "data_profile",
        "data_report",
    }


def test_profile_output_is_deterministic_and_json_safe(profile_context):
    project, data_artifact, service, _, workspace = profile_context

    first = service.profile(project["project_id"], data_artifact["artifact_id"])
    first_json = (workspace / "analysis" / "data_profile.json").read_bytes()
    first_report = (workspace / "analysis" / "data_report.md").read_bytes()
    second = service.profile(project["project_id"], data_artifact["artifact_id"])

    assert second == first
    assert (workspace / "analysis" / "data_profile.json").read_bytes() == first_json
    assert (workspace / "analysis" / "data_report.md").read_bytes() == first_report
    assert b"NaN" not in first_json


def test_rejects_non_data_artifact(profile_context):
    project, _, service, _, workspace = profile_context
    problem = workspace / "problem" / "original" / "prompt.txt"
    problem.parent.mkdir(parents=True)
    problem.write_text("Forecast", encoding="utf-8")
    problem_artifact = service.artifact_service.register(
        project["project_id"], "problem_input", "problem/original/prompt.txt"
    )

    with pytest.raises(ValueError, match="CSV data input"):
        service.profile(project["project_id"], problem_artifact["artifact_id"])
