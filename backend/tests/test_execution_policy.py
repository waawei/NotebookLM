import pytest

from services.approval_service import ApprovalService
from services.execution_policy import ExecutionPolicy
from services.experiment_contracts import ExecutionBatch
from services.modeling_store import ModelingStore
from services.project_environment_service import ProjectEnvironmentService


def policy_context(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    python_path = ProjectEnvironmentService().ensure_created(project)
    batch = ExecutionBatch(
        experiment_id="exp-0001",
        commands=[[str(python_path), "src/train.py", "--config", "experiments/exp-0001/config.json"]],
        timeout_seconds=60,
        max_output_bytes=1024,
        network_allowed=False,
        code_hash="a" * 64,
        input_hashes={"data/raw/sales.csv": "b" * 64},
    )
    approvals = ApprovalService(store)
    return ExecutionPolicy(approvals), approvals, project, batch


def test_policy_rejects_shell_and_external_paths(tmp_path):
    policy, _, project, batch = policy_context(tmp_path)
    bad = batch.model_copy(update={"commands": [["powershell", "-Command", "Remove-Item", "x"]]})

    with pytest.raises(ValueError, match="virtual environment Python"):
        policy.validate_batch(project, bad)


def test_changed_command_invalidates_execution_approval(tmp_path):
    policy, approvals, project, batch = policy_context(tmp_path)
    request = policy.request_execution(project, batch)
    approvals.decide(request["approval_id"], "approved", request["payload_hash"], "run")

    policy.require_execution_approval(project, batch)
    changed = batch.model_copy(update={"timeout_seconds": batch.timeout_seconds + 1})
    with pytest.raises(ValueError, match="approval"):
        policy.require_execution_approval(project, changed)


def test_install_batch_requires_explicit_network_permission(tmp_path):
    policy, _, project, batch = policy_context(tmp_path)
    install = batch.model_copy(
        update={
            "commands": [[str(ProjectEnvironmentService().ensure_created(project)), "-m", "pip", "install", "--requirement", "requirements.txt"]],
            "network_allowed": False,
        }
    )

    with pytest.raises(ValueError, match="network_allowed"):
        policy.validate_batch(project, install)


def test_policy_rejects_relative_path_escape_and_noncanonical_pip(tmp_path):
    policy, _, project, batch = policy_context(tmp_path)
    escaped = batch.model_copy(update={"commands": [[batch.commands[0][0], "..\\outside.py"]]})
    with pytest.raises(ValueError, match="escapes project workspace"):
        policy.validate_batch(project, escaped)

    pip_download = batch.model_copy(
        update={"commands": [[batch.commands[0][0], "-m", "pip", "download", "package"]], "network_allowed": True}
    )
    with pytest.raises(ValueError, match="pip command"):
        policy.validate_batch(project, pip_download)
