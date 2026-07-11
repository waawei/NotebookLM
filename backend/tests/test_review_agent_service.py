import asyncio
import json
from unittest.mock import AsyncMock

from services.artifact_service import ArtifactService
from services.modeling_store import ModelingStore
from services.paper_claim_service import PaperClaimService
from services.review_agent_service import ReviewAgentService


def test_review_blocks_unresolved_placeholders(tmp_path):
    workspace = tmp_path / "workspace"
    paper = workspace / "paper"
    paper.mkdir(parents=True)
    (paper / "draft.md").write_text("# Subproblem 1\n{{metric:exp-0001.validation_rmse}}", encoding="utf-8")
    (paper / "main.tex").write_text("\\begin{document}{{metric:exp-0001.validation_rmse}}\\end{document}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    reviewer = ReviewAgentService(store, artifacts, type("LLM", (), {})())
    reviewer.llm.generate = AsyncMock(return_value=json.dumps({"issues": []}))

    result = asyncio.run(reviewer.review(project["project_id"]))

    assert result["status"] == "failed"
    assert "unresolved_placeholder" in {item["code"] for item in result["issues"]}


def test_review_accepts_resolved_claims_and_invalidates_changed_paper(tmp_path):
    workspace = tmp_path / "workspace"
    paper = workspace / "paper"
    paper.mkdir(parents=True)
    markdown_path = paper / "draft.md"
    latex_path = paper / "main.tex"
    markdown_path.write_text("# Subproblem 1\nRMSE: {{metric:exp-0001.validation_rmse}}", encoding="utf-8")
    latex_path.write_text("\\begin{document}RMSE: {{metric:exp-0001.validation_rmse}}\\end{document}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    metrics_path = workspace / "experiments/exp-0001/metrics.json"
    metrics_path.parent.mkdir(parents=True)
    metrics_path.write_text('[{"name":"rmse","split":"validation","value":1.25}]', encoding="utf-8")
    store.create_experiment("exp-0001", project["project_id"], {
        "experiment_id": "exp-0001", "seed": 42, "target": "sales", "features": ["price"],
        "model": {"kind": "baseline", "parameters": {}}, "metrics": [{"name": "rmse", "direction": "minimize"}],
    }, "a" * 64)
    store.update_experiment_status("exp-0001", "completed")
    metric_artifact = artifacts.register(project["project_id"], "experiment_metrics", "experiments/exp-0001/metrics.json", source_experiment_id="exp-0001")
    markdown = artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    latex = artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    PaperClaimService(store).replace_for_paper(project["project_id"], markdown["artifact_id"], [{
        "placeholder": "{{metric:exp-0001.validation_rmse}}", "claim_type": "metric",
        "artifact_id": metric_artifact["artifact_id"], "experiment_id": "exp-0001",
        "metric_name": "validation_rmse", "rendered_value": "1.25",
    }])
    reviewer = ReviewAgentService(store, artifacts, type("LLM", (), {})())
    reviewer.llm.generate = AsyncMock(return_value=json.dumps({"issues": []}))

    passed = asyncio.run(reviewer.review(project["project_id"]))
    markdown_path.write_text("# Subproblem 1\nChanged", encoding="utf-8")

    assert passed["status"] == "passed"
    assert reviewer.current_paper_hash(project["project_id"]) != passed["paper_hash"]


def test_review_hash_changes_when_registered_bibliography_changes(tmp_path):
    workspace = tmp_path / "workspace"
    paper = workspace / "paper"
    paper.mkdir(parents=True)
    (paper / "draft.md").write_text("# Subproblem 1", encoding="utf-8")
    (paper / "main.tex").write_text("\\begin{document}OK\\end{document}", encoding="utf-8")
    bibliography = paper / "references.bib"
    bibliography.write_text("@article{one, title={One}}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    artifacts.register(project["project_id"], "paper_bibliography", "paper/references.bib")
    reviewer = ReviewAgentService(store, artifacts, type("LLM", (), {})())
    initial = reviewer.current_paper_hash(project["project_id"])
    bibliography.write_text("@article{two, title={Two}}", encoding="utf-8")

    assert reviewer.current_paper_hash(project["project_id"]) != initial
