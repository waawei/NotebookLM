import asyncio
import json

import pytest

from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.document_metadata_store import DocumentMetadataStore
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_role_service import ModelingRoleService
from services.modeling_store import ModelingStore


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    async def generate(self, prompt):
        self.prompts.append(prompt)
        return self.responses.pop(0)


def role_context(tmp_path, responses):
    workspace = tmp_path / "workspace"
    (workspace / "problem" / "original").mkdir(parents=True)
    (workspace / "analysis").mkdir()
    problem = workspace / "problem" / "original" / "赛题.txt"
    problem.write_text("预测未来销量，并说明约束。", encoding="utf-8")
    (workspace / "analysis" / "data_profile.json").write_text(
        json.dumps({"row_count": 3, "columns": {"target": {"dtype": "float64"}}}),
        encoding="utf-8",
    )
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    problem_artifact = artifacts.register(
        project["project_id"], "problem_input", "problem/original/赛题.txt"
    )
    profile_artifact = artifacts.register(
        project["project_id"], "data_profile", "analysis/data_profile.json"
    )
    lifecycle = ModelingAgentRunService(
        store, DocumentMetadataStore(str(tmp_path / "agents.db"))
    )
    llm = FakeLLM(responses)
    service = ModelingRoleService(
        store,
        artifacts,
        ApprovalService(store),
        lifecycle,
        llm,
    )
    return service, project, problem_artifact, profile_artifact, store, workspace, llm


def test_parses_utf8_problem_into_registered_structured_artifact(tmp_path):
    response = json.dumps(
        {
            "title": "销量预测",
            "subproblems": ["预测未来销量"],
            "objectives": ["最小化预测误差"],
            "constraints": ["仅使用给定数据"],
            "evaluation_requirements": ["RMSE"],
            "deliverables": ["论文", "代码"],
        },
        ensure_ascii=False,
    )
    service, project, problem, _, store, workspace, llm = role_context(
        tmp_path, [response]
    )

    result = asyncio.run(service.parse_problem(project["project_id"], problem["artifact_id"]))

    spec = json.loads(
        (workspace / "problem" / "problem_spec.json").read_text(encoding="utf-8")
    )
    assert spec["title"] == "销量预测"
    assert result["problem_spec"] == spec
    assert result["artifact"]["artifact_type"] == "problem_spec"
    assert "预测未来销量" in llm.prompts[0]
    assert {item["status"] for item in store.list_tasks(project["project_id"])} == {
        "completed"
    }


def test_model_plan_rejects_more_than_three_candidates_and_records_failure(tmp_path):
    response = json.dumps(
        {
            "problem_summary": "Forecast",
            "candidates": [
                {
                    "name": str(index),
                    "assumptions": [],
                    "features": [],
                    "algorithm": "linear",
                    "metrics": ["rmse"],
                    "risks": [],
                }
                for index in range(4)
            ],
        }
    )
    service, project, _, profile, store, workspace, _ = role_context(tmp_path, [response])
    (workspace / "problem" / "problem_spec.json").write_text(
        json.dumps({"title": "Forecast"}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="at most 3"):
        asyncio.run(
            service.create_model_plan(project["project_id"], profile["artifact_id"])
        )

    [task] = store.list_tasks(project["project_id"])
    assert task["status"] == "failed"
    assert task["retry_count"] == 1


def test_creates_json_markdown_and_hash_bound_approval_request(tmp_path):
    response = "```json\n" + json.dumps(
        {
            "problem_summary": "Forecast sales",
            "candidates": [
                {
                    "name": "Linear baseline",
                    "assumptions": ["stable relation"],
                    "features": ["category"],
                    "algorithm": "linear regression",
                    "metrics": ["rmse"],
                    "risks": ["drift"],
                }
            ],
        }
    ) + "\n```"
    service, project, _, profile, _, workspace, _ = role_context(tmp_path, [response])
    (workspace / "problem" / "problem_spec.json").write_text(
        json.dumps({"title": "Forecast"}), encoding="utf-8"
    )

    result = asyncio.run(
        service.create_model_plan(project["project_id"], profile["artifact_id"])
    )

    assert len(result["model_plan"]["candidates"]) == 1
    assert (workspace / "analysis" / "model_plan.json").is_file()
    assert "Linear baseline" in (
        workspace / "analysis" / "model_plan.md"
    ).read_text(encoding="utf-8")
    assert result["approval"]["payload"]["artifact_id"] == result["artifact"][
        "artifact_id"
    ]
    assert result["approval"]["payload"]["artifact_sha256"] == result["artifact"][
        "sha256"
    ]
