import json
from pathlib import Path

import pytest

from services.artifact_service import ArtifactService
from services.modeling_store import ModelingStore
from services.paper_placeholder_service import PaperPlaceholderService


@pytest.fixture
def paper_context(tmp_path):
    workspace = tmp_path / "workspace"
    metrics_path = workspace / "experiments" / "exp-0001" / "metrics.json"
    metrics_path.parent.mkdir(parents=True)
    metrics_path.write_text(json.dumps([
        {"name": "rmse", "split": "validation", "value": 1.25},
    ]), encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    store.create_experiment("exp-0001", project["project_id"], {
        "experiment_id": "exp-0001", "seed": 42, "target": "sales",
        "features": ["price"], "model": {"kind": "baseline", "parameters": {}},
        "metrics": [{"name": "rmse", "direction": "minimize"}],
    }, "a" * 64)
    store.update_experiment_status("exp-0001", "completed")
    artifact = ArtifactService(store).register(
        project["project_id"], "experiment_metrics",
        "experiments/exp-0001/metrics.json", source_experiment_id="exp-0001",
    )
    return project, store, artifact


def test_resolves_registered_metric_and_records_claim(paper_context):
    project, store, artifact = paper_context
    resolver = PaperPlaceholderService(store, ArtifactService(store))

    rendered, claims = resolver.resolve_markdown(
        project["project_id"], "RMSE is {{metric:exp-0001.validation_rmse}}."
    )

    assert rendered == "RMSE is 1.25."
    assert claims == [{
        "placeholder": "{{metric:exp-0001.validation_rmse}}", "claim_type": "metric",
        "artifact_id": artifact["artifact_id"], "experiment_id": "exp-0001",
        "metric_name": "validation_rmse", "rendered_value": "1.25",
    }]


def test_rejects_unknown_or_incomplete_experiment(paper_context):
    project, store, _ = paper_context
    resolver = PaperPlaceholderService(store, ArtifactService(store))

    with pytest.raises(ValueError, match="Unresolvable paper placeholder"):
        resolver.resolve_markdown(project["project_id"], "{{metric:exp-9999.validation_rmse}}")


def test_rejects_metric_artifact_changed_after_registration(paper_context):
    project, store, _ = paper_context
    metrics_path = Path(project["workspace_path"]) / "experiments/exp-0001/metrics.json"
    metrics_path.write_text(json.dumps([
        {"name": "rmse", "split": "validation", "value": 999},
    ]), encoding="utf-8")
    resolver = PaperPlaceholderService(store, ArtifactService(store))

    with pytest.raises(ValueError, match="Unresolvable paper placeholder"):
        resolver.resolve_markdown(
            project["project_id"], "{{metric:exp-0001.validation_rmse}}"
        )


def test_rejects_figure_linked_to_another_projects_experiment(paper_context, tmp_path):
    project, store, _ = paper_context
    other_workspace = tmp_path / "other-workspace"
    figure_path = Path(project["workspace_path"]) / "experiments/exp-0001/figure.png"
    figure_path.write_bytes(b"figure")
    other = store.create_project("Other", "other", str(other_workspace), None)
    store.create_experiment("exp-0002", other["project_id"], {
        "experiment_id": "exp-0002", "seed": 42, "target": "sales",
        "features": ["price"], "model": {"kind": "baseline", "parameters": {}},
        "metrics": [{"name": "rmse", "direction": "minimize"}],
    }, "b" * 64)
    store.update_experiment_status("exp-0002", "completed")
    artifact = ArtifactService(store).register(
        project["project_id"], "experiment_figure", "experiments/exp-0001/figure.png",
        source_experiment_id="exp-0002",
    )
    resolver = PaperPlaceholderService(store, ArtifactService(store))

    with pytest.raises(ValueError, match="Unresolvable paper placeholder"):
        resolver.resolve_markdown(project["project_id"], f"{{{{figure:{artifact['artifact_id']}}}}}")
