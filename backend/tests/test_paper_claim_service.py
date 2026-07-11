from services.modeling_store import ModelingStore
from services.paper_claim_service import PaperClaimService


def test_replaces_claims_for_one_paper_atomically(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    service = PaperClaimService(store)
    claims = [{
        "placeholder": "{{metric:exp-0001.validation_rmse}}", "claim_type": "metric",
        "artifact_id": "artifact-1", "experiment_id": "exp-0001",
        "metric_name": "validation_rmse", "rendered_value": "1.25",
    }]

    stored = service.replace_for_paper(project["project_id"], "paper-1", claims)
    replacement = service.replace_for_paper(project["project_id"], "paper-1", [])

    assert stored[0]["paper_artifact_id"] == "paper-1"
    assert stored[0]["rendered_value"] == "1.25"
    assert replacement == []
    assert store.list_paper_claims(project["project_id"]) == []
