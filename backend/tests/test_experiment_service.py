import json
import hashlib
from pathlib import Path

import pytest

from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.execution_policy import ExecutionPolicy
from services.experiment_contracts import ExecutionBatch
from services.experiment_service import ExperimentService
from services.modeling_store import ModelingStore
from services.project_environment_service import ProjectEnvironmentService


def experiment_context(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "experiments" / "exp-0001").mkdir(parents=True)
    (workspace / "figures").mkdir()
    script = workspace / "run.py"
    script.write_text(
        "import json, pathlib\nroot = pathlib.Path('experiments/exp-0001')\n"
        "(root / 'metrics.json').write_text(json.dumps([{'name':'rmse','value':1.0,'split':'validation'}]))\n"
        "(root / 'chart.png').write_bytes(b'figure')\n"
        "(root / 'artifacts.json').write_text(json.dumps(['experiments/exp-0001/chart.png']))\n",
        encoding="utf-8",
    )
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    environment = ProjectEnvironmentService()
    python_path = environment.ensure_created(project)
    source_hash = hashlib.sha256(script.read_bytes()).hexdigest()
    combined = hashlib.sha256(b"run.py\0" + source_hash.encode("ascii") + b"\0").hexdigest()
    batch = ExecutionBatch(
        experiment_id="exp-0001",
        commands=[[str(python_path), "run.py"]],
        timeout_seconds=30,
        max_output_bytes=4096,
        network_allowed=False,
        code_hash=combined,
        input_hashes={},
        source_hashes={"run.py": source_hash},
    )
    config = {
        "experiment_id": "exp-0001", "seed": 42, "target": "sales", "features": ["price"],
        "model": {"kind": "baseline", "parameters": {}},
        "metrics": [{"name": "rmse", "direction": "minimize"}],
    }
    store.create_experiment("exp-0001", project["project_id"], config, None)
    approvals = ApprovalService(store)
    policy = ExecutionPolicy(approvals, environment)
    request = policy.request_execution(project, batch)
    approvals.decide(request["approval_id"], "approved", request["payload_hash"])
    store.set_experiment_execution_batch(
        "exp-0001", request["payload_hash"], batch.model_dump(mode="json")
    )
    service = ExperimentService(store, ArtifactService(store), policy)
    return service, store, project


def test_experiment_execution_persists_immutable_metrics_environment_and_artifacts(tmp_path):
    service, store, project = experiment_context(tmp_path)

    result = service.execute(project["project_id"], "exp-0001")

    assert result["status"] == "completed"
    assert store.get_experiment("exp-0001")["pid"] is None
    artifacts = store.list_artifacts(project["project_id"])
    assert {item["artifact_type"] for item in artifacts} >= {"experiment_metrics", "experiment_log", "environment", "experiment_figure"}
    with pytest.raises(ValueError, match="not available for execution"):
        service.execute(project["project_id"], "exp-0001")


def test_execution_rejects_ticket_when_current_source_changes(tmp_path):
    service, _, project = experiment_context(tmp_path)
    source_path = Path(project["workspace_path"]) / "run.py"
    source_path.write_text("print('changed')\n", encoding="utf-8")

    with pytest.raises(ValueError, match="content"):
        service.execute(project["project_id"], "exp-0001")
