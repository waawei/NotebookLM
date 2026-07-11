import asyncio
import json
from unittest.mock import AsyncMock

from services.artifact_service import ArtifactService
from services.modeling_store import ModelingStore
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
