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


def test_non_finite_numeric_statistics_are_serialized_as_null(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "data" / "raw").mkdir(parents=True)
    (workspace / "analysis").mkdir()
    source = workspace / "data" / "raw" / "extremes.csv"
    source.write_text(
        "value,empty_numeric\ninf,\n-inf,\n1e308,\n1e308,\n",
        encoding="utf-8",
    )
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Extremes", "extremes", str(workspace), None)
    artifacts = ArtifactService(store)
    data_artifact = artifacts.register(
        project["project_id"], "data_input", "data/raw/extremes.csv"
    )

    result = DataProfileService(store, artifacts).profile(
        project["project_id"], data_artifact["artifact_id"]
    )

    numeric = result["columns"]["value"]["numeric"]
    assert numeric["min"] is None
    assert numeric["max"] is None
    assert numeric["mean"] is None
    assert numeric["std"] is None
    assert "numeric" not in result["columns"]["empty_numeric"]
    persisted = (workspace / "analysis" / "data_profile.json").read_text(
        encoding="utf-8"
    )
    assert "NaN" not in persisted
    assert "Infinity" not in persisted


def test_rejects_changed_missing_and_non_csv_sources(profile_context):
    project, data_artifact, service, _, workspace = profile_context
    source = workspace / "data" / "raw" / "train.csv"
    source.write_text("category,target\nchanged,9\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash does not match"):
        service.profile(project["project_id"], data_artifact["artifact_id"])

    source.unlink()
    with pytest.raises(ValueError, match="does not exist"):
        service.profile(project["project_id"], data_artifact["artifact_id"])

    text_source = workspace / "data" / "raw" / "train.txt"
    text_source.write_text("x\n1\n", encoding="utf-8")
    text_artifact = service.artifact_service.register(
        project["project_id"], "data_input", "data/raw/train.txt"
    )
    with pytest.raises(ValueError, match="CSV data input"):
        service.profile(project["project_id"], text_artifact["artifact_id"])


def test_rejects_source_replaced_by_external_symlink(profile_context, tmp_path):
    project, data_artifact, service, _, workspace = profile_context
    source = workspace / "data" / "raw" / "train.csv"
    outside = tmp_path / "outside.csv"
    outside.write_text("category,target\nexternal,99\n", encoding="utf-8")
    source.unlink()
    try:
        source.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")

    with pytest.raises(ValueError, match="outside project workspace"):
        service.profile(project["project_id"], data_artifact["artifact_id"])


@pytest.mark.parametrize("fail_at", [1, 2])
def test_artifact_registration_failure_rolls_back_outputs(
    profile_context, fail_at
):
    project, data_artifact, _, store, workspace = profile_context
    delegate = ArtifactService(store)

    class FailingArtifactService:
        def __init__(self):
            self.calls = 0

        def resolve(self, project_id, artifact_id):
            return delegate.resolve(project_id, artifact_id)

        def register(self, *args, **kwargs):
            self.calls += 1
            if self.calls == fail_at:
                raise RuntimeError("artifact index unavailable")
            return delegate.register(*args, **kwargs)

        def remove(self, project_id, artifact_id):
            return delegate.remove(project_id, artifact_id)

    service = DataProfileService(store, FailingArtifactService())
    with pytest.raises(RuntimeError, match="artifact index unavailable"):
        service.profile(project["project_id"], data_artifact["artifact_id"])

    assert not (workspace / "analysis" / "data_profile.json").exists()
    assert not (workspace / "analysis" / "data_report.md").exists()
    assert [item["artifact_type"] for item in store.list_artifacts(project["project_id"])] == [
        "data_input"
    ]


def test_second_output_write_failure_rolls_back_first_output(profile_context):
    project, data_artifact, service, store, workspace = profile_context

    class FailingReportService(DataProfileService):
        def _atomic_write(self, path, content):
            if path.name == "data_report.md":
                raise OSError("report disk failure")
            return super()._atomic_write(path, content)

    failing = FailingReportService(store, service.artifact_service)
    with pytest.raises(OSError, match="report disk failure"):
        failing.profile(project["project_id"], data_artifact["artifact_id"])

    assert not (workspace / "analysis" / "data_profile.json").exists()
    assert not (workspace / "analysis" / "data_report.md").exists()
