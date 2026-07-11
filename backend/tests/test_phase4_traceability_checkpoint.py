import asyncio
import json
from pathlib import Path

import pytest

from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.latex_service import LatexService
from services.modeling_store import ModelingStore
from services.paper_claim_service import PaperClaimService
from services.paper_placeholder_service import PaperPlaceholderService
from services.review_agent_service import ReviewAgentService


class ReviewLLM:
    async def generate(self, prompt):
        return json.dumps({"issues": []})


def test_phase4_traceable_paper_compiles_and_stale_content_is_rejected(tmp_path):
    workspace = tmp_path / "workspace"
    metrics = workspace / "experiments/exp-0001/metrics.json"
    figure = workspace / "experiments/exp-0001/figure.png"
    paper = workspace / "paper"
    metrics.parent.mkdir(parents=True)
    paper.mkdir()
    metrics.write_text('[{"name":"rmse","split":"validation","value":1.25}]', encoding="utf-8")
    figure.write_bytes(b"figure")
    markdown = paper / "draft.md"
    latex = paper / "main.tex"
    markdown.write_text("# Subproblem 1\nRMSE {{metric:exp-0001.validation_rmse}}\nFigure {{figure:FIGURE_ID}}", encoding="utf-8")
    latex.write_text("\\documentclass{article}\n\\begin{document}\nRMSE {{metric:exp-0001.validation_rmse}}\\par\nFigure {{figure:FIGURE_ID}}\n\\end{document}\n", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    store.create_experiment("exp-0001", project["project_id"], {
        "experiment_id": "exp-0001", "seed": 42, "target": "sales", "features": ["price"],
        "model": {"kind": "baseline", "parameters": {}}, "metrics": [{"name": "rmse", "direction": "minimize"}],
    }, "a" * 64)
    store.update_experiment_status("exp-0001", "completed")
    artifacts.register(project["project_id"], "experiment_metrics", "experiments/exp-0001/metrics.json", source_experiment_id="exp-0001")
    figure_artifact = artifacts.register(project["project_id"], "experiment_figure", "experiments/exp-0001/figure.png", source_experiment_id="exp-0001")
    markdown.write_text(markdown.read_text(encoding="utf-8").replace("FIGURE_ID", figure_artifact["artifact_id"]), encoding="utf-8")
    latex.write_text(latex.read_text(encoding="utf-8").replace("FIGURE_ID", figure_artifact["artifact_id"]), encoding="utf-8")
    markdown_artifact = artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    resolver = PaperPlaceholderService(store, artifacts)
    _, claims = resolver.resolve_markdown(project["project_id"], markdown.read_text(encoding="utf-8"))
    PaperClaimService(store).replace_for_paper(project["project_id"], markdown_artifact["artifact_id"], claims)
    reviewer = ReviewAgentService(store, artifacts, ReviewLLM())
    review = asyncio.run(reviewer.review(project["project_id"]))
    approvals = ApprovalService(store)
    latex_service = LatexService(store, artifacts, approvals, resolver)
    request = approvals.request(project["project_id"], "final_approval", latex_service.current_payload(project["project_id"]))
    approvals.decide(request["approval_id"], "approved", request["payload_hash"])

    result = latex_service.compile(project["project_id"])
    markdown.write_text("# Subproblem 1\nChanged", encoding="utf-8")

    assert review["status"] == "passed"
    assert Path(result["pdf_path"]).is_file()
    assert len(store.list_paper_claims(project["project_id"], markdown_artifact["artifact_id"])) == 2
    with pytest.raises(ValueError, match="review|approval"):
        latex_service.compile(project["project_id"])
