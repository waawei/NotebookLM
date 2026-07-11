import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from services.approval_service import ApprovalService, canonical_hash
from services.artifact_service import ArtifactService
from services.document_metadata_store import DocumentMetadataStore
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_code_agent_service import ModelingCodeAgentService
from services.modeling_store import ModelingStore


def code_agent_context(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "analysis").mkdir(parents=True)
    (workspace / "data" / "raw").mkdir(parents=True)
    (workspace / "analysis" / "model_plan.json").write_text(
        json.dumps({"candidates": [{"name": "Baseline", "features": ["price"]}]}), encoding="utf-8"
    )
    (workspace / "analysis" / "data_profile.json").write_text(
        json.dumps({"columns": {"price": {}, "sales": {}}}), encoding="utf-8"
    )
    (workspace / "data" / "raw" / "sales.csv").write_text("price,sales\n1,2\n", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    plan = artifacts.register(project["project_id"], "model_plan", "analysis/model_plan.json")
    artifacts.register(project["project_id"], "data_profile", "analysis/data_profile.json")
    artifacts.register(project["project_id"], "data_input", "data/raw/sales.csv")
    approval_payload = {
        "artifact_id": plan["artifact_id"],
        "artifact_sha256": plan["sha256"],
        "version": plan["version"],
    }
    approvals = ApprovalService(store)
    request = approvals.request(project["project_id"], "model_approval", approval_payload)
    approvals.decide(request["approval_id"], "approved", request["payload_hash"])
    lifecycle = ModelingAgentRunService(store, DocumentMetadataStore(str(tmp_path / "agents.db")))
    service = ModelingCodeAgentService(store, artifacts, approvals, lifecycle, type("LLM", (), {})())
    return service, project, workspace


def test_code_agent_rejects_undeclared_file(tmp_path):
    service, project, _ = code_agent_context(tmp_path)
    service.llm.generate = AsyncMock(
        return_value=json.dumps(
            {"files": [{"path": "../escape.py", "content": "print(1)"}], "commands": [["python", "src/train.py"]]}
        )
    )

    with pytest.raises(ValueError, match="allowed source path"):
        asyncio.run(service.prepare_experiment(project["project_id"], 0))


def test_code_agent_creates_hashed_bounded_experiment_draft(tmp_path):
    service, project, workspace = code_agent_context(tmp_path)
    service.llm.generate = AsyncMock(
        return_value=json.dumps(
            {
                "files": [
                    {"path": "src/train.py", "content": "print('train')\n"},
                    {"path": "tests/test_pipeline.py", "content": "def test_pipeline():\n    assert True\n"},
                    {"path": "requirements.txt", "content": "numpy==1.26.4\n"},
                ],
                "commands": [["python", "src/train.py", "--config", "experiments/exp-0001/config.json"]],
            }
        )
    )

    result = asyncio.run(service.prepare_experiment(project["project_id"], 0))

    assert result["experiment"]["experiment_id"] == "exp-0001"
    assert result["experiment"]["config"]["target"] == "sales"
    assert result["batch"]["commands"][0][0].endswith(".venv\\Scripts\\python.exe")
    assert result["batch"]["commands"][0][1:] == ["src/train.py", "--config", "experiments/exp-0001/config.json"]
    assert len(result["batch"]["code_hash"]) == 64
    assert (workspace / "src" / "train.py").is_file()
    assert (workspace / "experiments" / "exp-0001" / "config.json").is_file()
    assert "exp-0001" in (workspace / "reproduce.ps1").read_text(encoding="utf-8")


def test_code_agent_rejects_modified_input_and_incomplete_pipeline(tmp_path):
    service, project, workspace = code_agent_context(tmp_path)
    service.llm.generate = AsyncMock(
        return_value=json.dumps(
            {
                "files": [{"path": "requirements.txt", "content": "numpy==1.26.4\n"}],
                "commands": [["python", "src/train.py"]],
            }
        )
    )

    with pytest.raises(ValueError, match="pipeline test"):
        asyncio.run(service.prepare_experiment(project["project_id"], 0))

    (workspace / "data" / "raw" / "sales.csv").write_text("price,sales\n9,9\n", encoding="utf-8")
    service.llm.generate = AsyncMock(
        return_value=json.dumps(
            {
                "files": [
                    {"path": "src/train.py", "content": "print('train')\n"},
                    {"path": "tests/test_pipeline.py", "content": "def test_pipeline():\n    assert True\n"},
                    {"path": "requirements.txt", "content": "numpy==1.26.4\n"},
                ],
                "commands": [["python", "src/train.py"]],
            }
        )
    )

    with pytest.raises(ValueError, match="input hash does not match"):
        asyncio.run(service.prepare_experiment(project["project_id"], 0))


def test_code_hash_changes_when_generated_config_changes(tmp_path):
    service, project, _ = code_agent_context(tmp_path)
    files = [
        {"path": "src/train.py", "content": "print('train')\n"},
        {"path": "tests/test_pipeline.py", "content": "def test_pipeline():\n    assert True\n"},
        {"path": "requirements.txt", "content": "numpy==1.26.4\n"},
    ]
    service.llm.generate = AsyncMock(return_value=json.dumps({"files": files, "commands": [["python", "src/train.py"]]}))
    first = asyncio.run(service.prepare_experiment(project["project_id"], 0))
    service.llm.generate = AsyncMock(return_value=json.dumps({"files": files, "commands": [["python", "src/train.py"]]}))
    second = asyncio.run(service.prepare_experiment(project["project_id"], 0))

    assert first["experiment"]["config"]["experiment_id"] != second["experiment"]["config"]["experiment_id"]
    assert first["batch"]["code_hash"] != second["batch"]["code_hash"]
