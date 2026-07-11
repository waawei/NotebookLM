import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from services.artifact_service import ArtifactService
from services.modeling_store import ModelingStore
from services.paper_agent_service import PaperAgentService


@pytest.fixture
def writer(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "analysis").mkdir(parents=True)
    (workspace / "analysis/problem_spec.json").write_text("{}", encoding="utf-8")
    (workspace / "analysis/model_plan.json").write_text("{}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "problem_spec", "analysis/problem_spec.json")
    artifacts.register(project["project_id"], "model_plan", "analysis/model_plan.json")
    service = PaperAgentService(store, artifacts, type("LLM", (), {})())
    return service, project


def test_writer_rejects_literal_experiment_number(writer):
    service, project = writer
    service.llm.generate = AsyncMock(return_value=json.dumps({
        "markdown": "Validation RMSE was 1.25. " * 8,
        "latex": "\\documentclass{article}\\begin{document}Validation RMSE was 1.25.\\end{document}" * 3,
    }))

    with pytest.raises(ValueError, match="must use metric placeholders"):
        asyncio.run(service.create_draft(project["project_id"]))


def test_writer_accepts_metric_placeholder(writer):
    service, project = writer
    payload = {
        "markdown": ("# Results\nRMSE: {{metric:exp-0001.validation_rmse}}. " * 8),
        "latex": ("\\documentclass{article}\\begin{document}RMSE: {{metric:exp-0001.validation_rmse}}.\\end{document}" * 3),
    }
    service.llm.generate = AsyncMock(return_value=json.dumps(payload))

    result = asyncio.run(service.create_draft(project["project_id"]))

    assert result["markdown_artifact"]["artifact_type"] == "paper_markdown"
    assert "{{metric:exp-0001.validation_rmse}}" in (
        Path(project["workspace_path"]) / "paper/draft.md"
    ).read_text(encoding="utf-8")
