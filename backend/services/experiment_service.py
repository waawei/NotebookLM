import json
import hashlib
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from services.environment_capture import EnvironmentCapture
from services.experiment_contracts import ExecutionBatch, MetricRecord
from services.restricted_runner import RestrictedRunner
from services.approval_service import canonical_hash


class ExperimentService:
    def __init__(self, store, artifact_service, execution_policy, runner=None, environment_capture=None):
        self.store = store
        self.artifact_service = artifact_service
        self.execution_policy = execution_policy
        self.runner = runner or RestrictedRunner()
        self.environment_capture = environment_capture or EnvironmentCapture()

    def execute(self, project_id: str, experiment_id: str) -> dict:
        project = self.store.get_project(project_id)
        experiment = self.store.get_experiment(experiment_id)
        if not project or not experiment or experiment["project_id"] != project_id:
            raise ValueError("Experiment not found")
        if experiment["status"] != "prepared" or "execution_batch" not in experiment:
            raise ValueError("Experiment is not available for execution")
        batch = ExecutionBatch.model_validate(experiment["execution_batch"])
        if batch.experiment_id != experiment_id or experiment["execution_payload_hash"] != canonical_hash(batch.model_dump(mode="json")):
            raise ValueError("Execution approval does not match current content")
        root = Path(project["workspace_path"]).resolve()
        self._verify_current_content(root, batch)
        self.execution_policy.require_execution_approval(project, batch)
        directory = root / "experiments" / experiment_id
        if not directory.is_dir():
            raise ValueError("Experiment directory is unavailable")
        self.store.claim_experiment(experiment_id, datetime.now().isoformat())
        try:
            logs = []
            exit_code = 0
            for command in batch.commands:
                result = self.runner.run(
                    command, root, batch.timeout_seconds, batch.max_output_bytes, batch.network_allowed,
                    on_started=lambda pid: self.store.update_experiment_status(experiment_id, "running", pid=pid),
                )
                logs.append(result.stdout + result.stderr)
                exit_code = result.exit_code
                if result.error_code:
                    raise ValueError(result.error_code)
            (directory / "run.log").write_text("".join(logs), encoding="utf-8")
            self._metrics(directory / "metrics.json")
            environment = self.environment_capture.capture(batch.commands[0][0], root)
            (directory / "environment.json").write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")
            self._register_outputs(project_id, experiment_id, directory, root)
            self.store.update_experiment_status(experiment_id, "completed", pid=None, exit_code=exit_code, finished_at=datetime.now().isoformat())
            return self.store.get_experiment(experiment_id)
        except Exception as error:
            code = self._error_code(error)
            self.store.update_experiment_status(experiment_id, "failed", pid=None, exit_code=locals().get("exit_code"), error_code=code, finished_at=datetime.now().isoformat())
            raise ValueError(code) from error

    @staticmethod
    def _verify_current_content(root: Path, batch: ExecutionBatch) -> None:
        source_hashes = {}
        for relative, expected in batch.source_hashes.items():
            path = (root / relative).resolve()
            if path == root or root not in path.parents or not path.is_file():
                raise ValueError("Execution approval does not match current content")
            source_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            if source_hashes[relative] != expected:
                raise ValueError("Execution approval does not match current content")
        digest = hashlib.sha256()
        for relative, value in sorted(source_hashes.items()):
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(value.encode("ascii"))
            digest.update(b"\0")
        if digest.hexdigest() != batch.code_hash:
            raise ValueError("Execution approval does not match current content")
        for relative, expected in batch.input_hashes.items():
            path = (root / relative).resolve()
            if path == root or root not in path.parents or not path.is_file():
                raise ValueError("Execution approval does not match current content")
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("Execution approval does not match current content")

    @staticmethod
    def _metrics(path: Path) -> list[MetricRecord]:
        if not path.is_file():
            raise ValueError("schema_error")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, list) or not raw:
                raise ValueError
            return [MetricRecord.model_validate(item) for item in raw]
        except (json.JSONDecodeError, ValidationError, ValueError) as error:
            raise ValueError("schema_error") from error

    def _register_outputs(self, project_id: str, experiment_id: str, directory: Path, root: Path) -> None:
        try:
            declared = json.loads((directory / "artifacts.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("schema_error") from error
        if not isinstance(declared, list) or not all(isinstance(path, str) for path in declared):
            raise ValueError("schema_error")
        outputs = [
            ("experiment_metrics", directory / "metrics.json"),
            ("experiment_log", directory / "run.log"),
            ("environment", directory / "environment.json"),
        ]
        for relative in declared:
            path = (root / relative).resolve()
            if (
                path == directory
                or directory not in path.parents
                or not path.is_file()
            ):
                raise ValueError("schema_error")
            kind = "experiment_figure" if path.suffix.lower() in {".png", ".jpg", ".svg"} else "experiment_table"
            outputs.append((kind, path))
        registered = []
        try:
            for kind, path in outputs:
                registered.append(
                    self.artifact_service.register(
                        project_id,
                        kind,
                        path.relative_to(root).as_posix(),
                        source_experiment_id=experiment_id,
                    )
                )
        except Exception:
            for artifact in reversed(registered):
                self.artifact_service.remove(project_id, artifact["artifact_id"])
            raise

    @staticmethod
    def _error_code(error: Exception) -> str:
        value = str(error)
        return value if value in {"code_error", "resource_error", "schema_error"} else "experiment_error"
