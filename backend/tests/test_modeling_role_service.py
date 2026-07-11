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
        json.dumps(
            {
                "title": "Forecast",
                "subproblems": [],
                "objectives": [],
                "constraints": [],
                "evaluation_requirements": [],
                "deliverables": [],
            }
        ),
        encoding="utf-8",
    )
    service.artifact_service.register(
        project["project_id"], "problem_spec", "problem/problem_spec.json"
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
        json.dumps(
            {
                "title": "Forecast",
                "subproblems": [],
                "objectives": [],
                "constraints": [],
                "evaluation_requirements": [],
                "deliverables": [],
            }
        ),
        encoding="utf-8",
    )
    service.artifact_service.register(
        project["project_id"], "problem_spec", "problem/problem_spec.json"
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


def test_three_real_role_failures_reuse_and_block_one_task(tmp_path):
    service, project, problem, _, store, _, _ = role_context(
        tmp_path, ["not json", "not json", "not json"]
    )

    for _ in range(3):
        with pytest.raises(ValueError, match="not valid JSON"):
            asyncio.run(
                service.parse_problem(project["project_id"], problem["artifact_id"])
            )

    [task] = store.list_tasks(project["project_id"])
    assert task["retry_count"] == 3
    assert task["status"] == "blocked"
    assert len(service.run_service.agent_store.list_agent_runs(project["project_id"])) == 3


def test_role_rejects_modified_registered_inputs(tmp_path):
    response = json.dumps(
        {
            "title": "Forecast",
            "subproblems": [],
            "objectives": [],
            "constraints": [],
            "evaluation_requirements": [],
            "deliverables": [],
        }
    )
    service, project, problem, profile, _, workspace, _ = role_context(
        tmp_path, [response]
    )
    (workspace / problem["relative_path"]).write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="hash does not match"):
        asyncio.run(service.parse_problem(project["project_id"], problem["artifact_id"]))

    (workspace / "problem" / "problem_spec.json").write_text(
        json.dumps(
            {
                "title": "Forecast",
                "subproblems": [],
                "objectives": [],
                "constraints": [],
                "evaluation_requirements": [],
                "deliverables": [],
            }
        ),
        encoding="utf-8",
    )
    service.artifact_service.register(
        project["project_id"], "problem_spec", "problem/problem_spec.json"
    )
    (workspace / profile["relative_path"]).write_text('{"changed": true}', encoding="utf-8")
    with pytest.raises(ValueError, match="hash does not match"):
        asyncio.run(
            service.create_model_plan(project["project_id"], profile["artifact_id"])
        )


def test_provider_failure_is_sanitized_in_exception_and_run_history(tmp_path):
    class FailingLLM:
        async def generate(self, prompt):
            raise RuntimeError(
                "Bearer secret-token-123456 at C:\\private\\provider.txt using sk-secret-123456789"
            )

    service, project, problem, _, _, _, _ = role_context(tmp_path, [])
    service.llm = FailingLLM()

    with pytest.raises(ValueError) as raised:
        asyncio.run(service.parse_problem(project["project_id"], problem["artifact_id"]))

    [run] = service.run_service.agent_store.list_agent_runs(project["project_id"])
    combined = str(raised.value) + str(run)
    assert "secret-token" not in combined
    assert "sk-secret" not in combined
    assert "private" not in combined
    assert "RuntimeError" in str(raised.value)


def test_plan_approval_failure_rolls_back_outputs_and_artifacts(tmp_path):
    response = json.dumps(
        {
            "problem_summary": "Forecast",
            "candidates": [
                {
                    "name": "Baseline",
                    "assumptions": [],
                    "features": [],
                    "algorithm": "linear",
                    "metrics": ["rmse"],
                    "risks": [],
                }
            ],
        }
    )
    service, project, _, profile, store, workspace, _ = role_context(tmp_path, [response])
    spec_path = workspace / "problem" / "problem_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "title": "Forecast",
                "subproblems": [],
                "objectives": [],
                "constraints": [],
                "evaluation_requirements": [],
                "deliverables": [],
            }
        ),
        encoding="utf-8",
    )
    service.artifact_service.register(
        project["project_id"], "problem_spec", "problem/problem_spec.json"
    )

    class FailingApprovalService:
        def request(self, *args, **kwargs):
            raise RuntimeError("approval store unavailable")

    service.approval_service = FailingApprovalService()
    with pytest.raises(ValueError, match="RuntimeError"):
        asyncio.run(
            service.create_model_plan(project["project_id"], profile["artifact_id"])
        )

    assert not (workspace / "analysis" / "model_plan.json").exists()
    assert not (workspace / "analysis" / "model_plan.md").exists()
    assert not {
        "model_plan",
        "model_plan_report",
    } & {item["artifact_type"] for item in store.list_artifacts(project["project_id"])}


@pytest.mark.parametrize("fail_at", [1, 2])
def test_plan_artifact_failure_rolls_back_outputs(tmp_path, fail_at):
    response = json.dumps(
        {
            "problem_summary": "Forecast",
            "candidates": [
                {
                    "name": "Baseline",
                    "assumptions": [],
                    "features": [],
                    "algorithm": "linear",
                    "metrics": ["rmse"],
                    "risks": [],
                }
            ],
        }
    )
    service, project, _, profile, store, workspace, _ = role_context(tmp_path, [response])
    spec = workspace / "problem" / "problem_spec.json"
    spec.write_text(
        json.dumps(
            {
                "title": "Forecast",
                "subproblems": [],
                "objectives": [],
                "constraints": [],
                "evaluation_requirements": [],
                "deliverables": [],
            }
        ),
        encoding="utf-8",
    )
    service.artifact_service.register(
        project["project_id"], "problem_spec", "problem/problem_spec.json"
    )
    delegate = service.artifact_service

    class FailingArtifactService:
        def __init__(self):
            self.calls = 0

        def resolve(self, *args, **kwargs):
            return delegate.resolve(*args, **kwargs)

        def register(self, *args, **kwargs):
            self.calls += 1
            if self.calls == fail_at:
                raise RuntimeError("artifact store unavailable")
            return delegate.register(*args, **kwargs)

        def remove(self, *args, **kwargs):
            return delegate.remove(*args, **kwargs)

    service.artifact_service = FailingArtifactService()
    with pytest.raises(ValueError, match="RuntimeError"):
        asyncio.run(
            service.create_model_plan(project["project_id"], profile["artifact_id"])
        )

    assert not (workspace / "analysis" / "model_plan.json").exists()
    assert not (workspace / "analysis" / "model_plan.md").exists()
    assert not {
        "model_plan",
        "model_plan_report",
    } & {item["artifact_type"] for item in store.list_artifacts(project["project_id"])}


def test_plan_completion_failure_removes_approval_artifacts_and_outputs(tmp_path):
    response = json.dumps(
        {
            "problem_summary": "Forecast",
            "candidates": [
                {
                    "name": "Baseline",
                    "assumptions": [],
                    "features": [],
                    "algorithm": "linear",
                    "metrics": ["rmse"],
                    "risks": [],
                }
            ],
        }
    )
    service, project, _, profile, store, workspace, _ = role_context(tmp_path, [response])
    spec = workspace / "problem" / "problem_spec.json"
    spec.write_text(
        json.dumps(
            {
                "title": "Forecast",
                "subproblems": [],
                "objectives": [],
                "constraints": [],
                "evaluation_requirements": [],
                "deliverables": [],
            }
        ),
        encoding="utf-8",
    )
    service.artifact_service.register(
        project["project_id"], "problem_spec", "problem/problem_spec.json"
    )
    delegate = service.run_service

    class CompletionFailingRunService:
        agent_store = delegate.agent_store

        def start(self, *args, **kwargs):
            return delegate.start(*args, **kwargs)

        def complete(self, *args, **kwargs):
            raise RuntimeError("completion unavailable")

        def fail(self, *args, **kwargs):
            return delegate.fail(*args, **kwargs)

    service.run_service = CompletionFailingRunService()
    with pytest.raises(ValueError, match="RuntimeError"):
        asyncio.run(
            service.create_model_plan(project["project_id"], profile["artifact_id"])
        )

    assert store.list_approval_requests(project["project_id"]) == []
    assert not (workspace / "analysis" / "model_plan.json").exists()
    assert not (workspace / "analysis" / "model_plan.md").exists()
    assert not {
        "model_plan",
        "model_plan_report",
    } & {item["artifact_type"] for item in store.list_artifacts(project["project_id"])}
