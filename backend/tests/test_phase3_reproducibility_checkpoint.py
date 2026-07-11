import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.document_metadata_store import DocumentMetadataStore
from services.execution_policy import ExecutionPolicy
from services.experiment_service import ExperimentService
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_code_agent_service import ModelingCodeAgentService
from services.modeling_store import ModelingStore


class DeterministicProgrammingLLM:
    def __init__(self):
        self.calls = 0

    async def generate(self, prompt):
        self.calls += 1
        value = 1.0 if self.calls in {1, 3} else 0.5
        return json.dumps(
            {
                "files": [
                    {
                        "path": "src/train.py",
                        "content": (
                            "import json\nfrom pathlib import Path\n"
                            f"root = Path('experiments/exp-{self.calls:04d}')\n"
                            f"(root / 'metrics.json').write_text(json.dumps([{{'name':'rmse','value':{value},'split':'validation'}}]))\n"
                            "Path('figures').mkdir(exist_ok=True)\n"
                            f"Path('figures/exp-{self.calls:04d}.png').write_bytes(b'figure')\n"
                            f"(root / 'artifacts.json').write_text(json.dumps(['figures/exp-{self.calls:04d}.png']))\n"
                        ),
                    },
                    {"path": "tests/test_pipeline.py", "content": "def test_pipeline():\n    assert True\n"},
                    {"path": "requirements.txt", "content": "\n"},
                ],
                "commands": [["python", "src/train.py"]],
            }
        )


def checkpoint_context(tmp_path):
    workspace = tmp_path / "workspace"
    for relative in ("analysis", "data/raw", "src", "tests", "experiments", "figures"):
        (workspace / relative).mkdir(parents=True, exist_ok=True)
    (workspace / "analysis" / "data_profile.json").write_text("{}", encoding="utf-8")
    (workspace / "data" / "raw" / "sales.csv").write_text("price,sales\n1,1\n", encoding="utf-8")
    plan = {
        "candidates": [
            {"name": "Baseline", "features": ["price"], "algorithm": "baseline", "metrics": ["rmse"]},
            {"name": "Candidate", "features": ["price"], "algorithm": "candidate", "metrics": ["rmse"]},
        ]
    }
    (workspace / "analysis" / "model_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    plan_artifact = artifacts.register(project["project_id"], "model_plan", "analysis/model_plan.json")
    artifacts.register(project["project_id"], "data_profile", "analysis/data_profile.json")
    artifacts.register(project["project_id"], "data_input", "data/raw/sales.csv")
    approvals = ApprovalService(store)
    model_request = approvals.request(
        project["project_id"],
        "model_approval",
        {"artifact_id": plan_artifact["artifact_id"], "artifact_sha256": plan_artifact["sha256"], "version": plan_artifact["version"]},
    )
    approvals.decide(model_request["approval_id"], "approved", model_request["payload_hash"])
    lifecycle = ModelingAgentRunService(store, DocumentMetadataStore(str(tmp_path / "agents.db")))
    agent = ModelingCodeAgentService(store, artifacts, approvals, lifecycle, DeterministicProgrammingLLM())
    policy = ExecutionPolicy(approvals)
    runner = ExperimentService(store, artifacts, policy)
    return project, store, approvals, agent, policy, runner, workspace


def approve_and_run(project, store, approvals, agent, policy, runner, candidate_index):
    prepared = asyncio.run(agent.prepare_experiment(project["project_id"], candidate_index))
    batch = prepared["batch"]
    request = policy.request_execution(project, __import__("services.experiment_contracts", fromlist=["ExecutionBatch"]).ExecutionBatch.model_validate(batch))
    approvals.decide(request["approval_id"], "approved", request["payload_hash"])
    store.set_experiment_execution_batch(prepared["experiment"]["experiment_id"], request["payload_hash"], batch)
    return runner.execute(project["project_id"], prepared["experiment"]["experiment_id"])


def test_phase3_reproducibility_and_stale_command_checkpoint(tmp_path):
    project, store, approvals, agent, policy, runner, workspace = checkpoint_context(tmp_path)

    baseline = approve_and_run(project, store, approvals, agent, policy, runner, 0)
    baseline_directory = workspace / "experiments" / baseline["experiment_id"]
    baseline_bytes = {path.name: path.read_bytes() for path in baseline_directory.iterdir()}
    candidate = approve_and_run(project, store, approvals, agent, policy, runner, 1)
    repeated = approve_and_run(project, store, approvals, agent, policy, runner, 0)

    def validation_metric(experiment_id):
        metrics = json.loads((workspace / "experiments" / experiment_id / "metrics.json").read_text(encoding="utf-8"))
        return next(item["value"] for item in metrics if item["split"] == "validation")

    assert baseline["status"] == candidate["status"] == repeated["status"] == "completed"
    assert abs(validation_metric(baseline["experiment_id"]) - validation_metric(repeated["experiment_id"])) <= 1e-9
    assert {path.name: path.read_bytes() for path in baseline_directory.iterdir()} == baseline_bytes
    assert any(item["artifact_type"] == "experiment_figure" for item in store.list_artifacts(project["project_id"]))

    stale = store.get_experiment(repeated["experiment_id"])["execution_batch"]
    stale["timeout_seconds"] += 1
    store.update_experiment_status(repeated["experiment_id"], "prepared")
    store.set_experiment_execution_batch(repeated["experiment_id"], hashlib.sha256(b"stale").hexdigest(), stale)
    with pytest.raises(ValueError, match="approval"):
        runner.execute(project["project_id"], repeated["experiment_id"])
