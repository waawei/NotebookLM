import asyncio
import hashlib
import json
import stat
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from api import modeling
from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.data_profile_service import DataProfileService
from services.document_metadata_store import DocumentMetadataStore
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_gate_service import ModelingGateService
from services.modeling_input_service import ModelingInputService
from services.modeling_project_service import ModelingProjectService
from services.modeling_role_service import ModelingRoleService
from services.modeling_store import ModelingStore
from services.modeling_workspace import ModelingWorkspaceService


class DeterministicModelingLLM:
    def __init__(self):
        self.responses = [
            json.dumps(
                {
                    "title": "UTF-8 销量预测",
                    "subproblems": ["预测目标销量"],
                    "objectives": ["最小化预测误差"],
                    "constraints": ["仅使用给定 CSV"],
                    "evaluation_requirements": ["RMSE"],
                    "deliverables": ["论文", "代码"],
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "problem_summary": "基于分类特征预测数值销量",
                    "candidates": [
                        {
                            "name": "均值基线",
                            "assumptions": ["目标均值稳定"],
                            "features": ["category"],
                            "algorithm": "mean baseline",
                            "metrics": ["rmse"],
                            "risks": ["分布漂移"],
                        },
                        {
                            "name": "线性候选",
                            "assumptions": ["类别效应可编码"],
                            "features": ["category"],
                            "algorithm": "linear regression",
                            "metrics": ["rmse"],
                            "risks": ["样本量较小"],
                        },
                    ],
                },
                ensure_ascii=False,
            ),
        ]

    async def generate(self, prompt):
        return self.responses.pop(0)


def test_real_utf8_csv_checkpoint_and_stale_plan_conflict(tmp_path, monkeypatch):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    artifacts = ArtifactService(store)
    approvals = ApprovalService(store)
    workspace_service = ModelingWorkspaceService(
        str(tmp_path / "projects"), str(tmp_path / "application")
    )
    agent_store = DocumentMetadataStore(str(tmp_path / "agents.db"))
    project_service = ModelingProjectService(
        store,
        workspace_service,
        agent_store=agent_store,
        gate_service=ModelingGateService(store, approvals),
    )
    inputs = ModelingInputService(store, artifacts, max_file_size=1024 * 1024)
    profiles = DataProfileService(store, artifacts)
    roles = ModelingRoleService(
        store,
        artifacts,
        approvals,
        ModelingAgentRunService(store, agent_store),
        DeterministicModelingLLM(),
    )
    monkeypatch.setattr(modeling, "project_service", project_service)
    monkeypatch.setattr(modeling, "artifact_service", artifacts)
    monkeypatch.setattr(modeling, "approval_service", approvals)
    monkeypatch.setattr(modeling, "input_service", inputs)
    monkeypatch.setattr(modeling, "profile_service", profiles)
    monkeypatch.setattr(modeling, "role_service", roles)

    project = asyncio.run(
        modeling.create_project(modeling.ProjectCreate(name="真实 UTF-8 检查点"))
    )
    problem_bytes = "预测未来销量，并说明约束与 RMSE 评价要求。".encode("utf-8")
    csv_bytes = "category,target\nA,1\nA,1\nB,\n".encode("utf-8")
    problem_artifact = asyncio.run(
        modeling.upload_input(
            project["project_id"],
            UploadFile(filename="赛题.txt", file=BytesIO(problem_bytes)),
            "problem",
        )
    )
    data_artifact = asyncio.run(
        modeling.upload_input(
            project["project_id"],
            UploadFile(filename="训练数据.csv", file=BytesIO(csv_bytes)),
            "data",
        )
    )

    workspace = tmp_path / "projects" / project["slug"]
    problem_raw = workspace / "problem" / "original" / "赛题.txt"
    data_raw = workspace / "data" / "raw" / "训练数据.csv"
    assert problem_raw.read_bytes() == problem_bytes
    assert data_raw.read_bytes() == csv_bytes
    assert not problem_raw.stat().st_mode & stat.S_IWRITE
    assert not data_raw.stat().st_mode & stat.S_IWRITE
    problem_manifest = json.loads(
        (workspace / "problem" / "input_manifest.json").read_text(encoding="utf-8")
    )
    data_manifest = json.loads(
        (workspace / "data" / "data_manifest.json").read_text(encoding="utf-8")
    )
    assert problem_manifest["files"][0]["sha256"] == hashlib.sha256(
        problem_bytes
    ).hexdigest()
    assert data_manifest["files"][0]["sha256"] == hashlib.sha256(csv_bytes).hexdigest()

    assert asyncio.run(modeling.advance_project(project["project_id"]))["state"] == "problem_parsing"
    asyncio.run(modeling.parse_problem(project["project_id"]))
    assert asyncio.run(modeling.advance_project(project["project_id"]))["state"] == "data_profiling"
    profile = asyncio.run(
        modeling.profile_data(project["project_id"], data_artifact["artifact_id"])
    )
    assert profile["duplicate_rows"] == 1
    assert profile["columns"]["target"]["missing"] == 1
    assert asyncio.run(modeling.advance_project(project["project_id"]))["state"] == "model_planning"
    plan_result = asyncio.run(modeling.create_model_plan(project["project_id"]))
    assert len(plan_result["model_plan"]["candidates"]) == 2
    assert asyncio.run(modeling.advance_project(project["project_id"]))["state"] == "model_approval_pending"
    approval = plan_result["approval"]
    asyncio.run(
        modeling.decide_approval(
            project["project_id"],
            approval["approval_id"],
            modeling.ApprovalDecision(
                decision="approved",
                payload_hash=approval["payload_hash"],
                comment="批准基线与候选方案",
            ),
        )
    )

    plan_path = workspace / "analysis" / "model_plan.json"
    registered_plan = plan_path.read_bytes()
    plan_path.write_text('{"tampered": true}\n', encoding="utf-8")
    with pytest.raises(HTTPException) as conflict:
        asyncio.run(modeling.advance_project(project["project_id"]))
    assert conflict.value.status_code == 409
    assert store.get_project(project["project_id"])["state"] == "model_approval_pending"

    plan_path.write_bytes(registered_plan)
    advanced = asyncio.run(modeling.advance_project(project["project_id"]))
    assert advanced["state"] == "experiment_implementation"
    assert problem_artifact["artifact_type"] == "problem_input"
    kinds = {item["artifact_type"] for item in store.list_artifacts(project["project_id"])}
    assert {
        "problem_spec",
        "data_profile",
        "data_report",
        "model_plan",
        "model_plan_report",
    } <= kinds
    for relative_path in (
        "problem/problem_spec.json",
        "analysis/data_profile.json",
        "analysis/data_report.md",
        "analysis/model_plan.json",
        "analysis/model_plan.md",
    ):
        assert (workspace / relative_path).is_file()
