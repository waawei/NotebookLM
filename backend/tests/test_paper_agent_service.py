import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from services.artifact_service import ArtifactService
from services.approval_service import ApprovalService
from services.document_metadata_store import DocumentMetadataStore
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_store import ModelingStore
from services.paper_agent_service import PaperAgentService


@pytest.fixture
def writer(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "analysis").mkdir(parents=True)
    (workspace / "analysis/problem_spec.json").write_text('{"title":"Forecast"}', encoding="utf-8")
    (workspace / "analysis/model_plan.json").write_text('{"candidates":[{"name":"Baseline"}]}', encoding="utf-8")
    metrics = workspace / "experiments/exp-0001/metrics.json"
    metrics.parent.mkdir(parents=True)
    metrics.write_text('[{"name":"rmse","split":"validation","value":1.25}]', encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "problem_spec", "analysis/problem_spec.json")
    plan = artifacts.register(project["project_id"], "model_plan", "analysis/model_plan.json")
    approvals = ApprovalService(store)
    request = approvals.request(project["project_id"], "model_approval", {
        "artifact_id": plan["artifact_id"], "artifact_sha256": plan["sha256"], "version": plan["version"],
    })
    approvals.decide(request["approval_id"], "approved", request["payload_hash"])
    store.create_experiment("exp-0001", project["project_id"], {
        "experiment_id": "exp-0001", "seed": 42, "target": "sales", "features": ["price"],
        "model": {"kind": "baseline", "parameters": {}}, "metrics": [{"name":"rmse","direction":"minimize"}],
    }, "a" * 64)
    store.update_experiment_status("exp-0001", "completed")
    artifacts.register(project["project_id"], "experiment_metrics", "experiments/exp-0001/metrics.json", source_experiment_id="exp-0001")
    lifecycle = ModelingAgentRunService(store, DocumentMetadataStore(str(tmp_path / "agents.db")))
    service = PaperAgentService(store, artifacts, approvals, lifecycle, type("LLM", (), {})())
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
    assert service.store.list_tasks(project["project_id"])[0]["status"] == "completed"


def test_writer_requires_approved_plan_and_completed_experiment(writer):
    service, project = writer
    service.store.update_experiment_status("exp-0001", "failed")

    with pytest.raises(ValueError, match="completed experiment"):
        asyncio.run(service.create_draft(project["project_id"]))


def test_writer_supplies_verified_problem_and_plan_content(writer):
    service, project = writer
    payload = {
        "markdown": "# Results\nRMSE: {{metric:exp-0001.validation_rmse}}. " * 8,
        "latex": "\\documentclass{article}\\begin{document}RMSE: {{metric:exp-0001.validation_rmse}}.\\end{document}" * 3,
    }
    service.llm.generate = AsyncMock(return_value=json.dumps(payload))

    asyncio.run(service.create_draft(project["project_id"]))

    prompt = service.llm.generate.await_args.args[0]
    assert '{"title":"Forecast"}' in prompt
    assert '{"candidates":[{"name":"Baseline"}]}' in prompt


@pytest.mark.parametrize("result", ["Validation loss was 1.25.", "Validation score was 88%.", "Validation error was 1e-3."])
def test_writer_rejects_unbound_result_numbers(writer, result):
    service, project = writer
    service.llm.generate = AsyncMock(return_value=json.dumps({
        "markdown": (result + " ") * 8,
        "latex": ("\\documentclass{article}\\begin{document}" + result + "\\end{document}") * 3,
    }))

    with pytest.raises(ValueError, match="must use metric placeholders"):
        asyncio.run(service.create_draft(project["project_id"]))
