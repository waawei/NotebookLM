import hashlib
import json
from pathlib import Path

from services.approval_service import canonical_hash
from services.experiment_contracts import MetricRecord


class ModelingGateService:
    def __init__(self, store, approval_service):
        self.store = store
        self.approval_service = approval_service

    def require_exit(self, project_id: str, state: str) -> None:
        artifacts = self.store.list_artifacts(project_id)
        kinds = {item["artifact_type"] for item in artifacts}
        required = {
            "problem_parsing": {"problem_spec"},
            "data_profiling": {"data_profile", "data_report"},
            "model_planning": {"model_plan"},
        }
        missing = required.get(state, set()) - kinds
        if missing:
            raise ValueError("Missing required artifacts: " + ", ".join(sorted(missing)))
        if state != "model_approval_pending":
            if state == "result_validation":
                self._require_experiment_results(project_id)
            return

        plans = [item for item in artifacts if item["artifact_type"] == "model_plan"]
        if not plans:
            raise ValueError("Missing required model plan artifact")
        plan = max(plans, key=lambda item: (item["created_at"], item["artifact_id"]))
        project = self.store.get_project(project_id)
        root = Path(project["workspace_path"]).resolve()
        target = (root / plan["relative_path"]).resolve()
        if target == root or root not in target.parents or not target.is_file():
            raise ValueError("Current model plan artifact is unavailable")
        payload = {
            "artifact_id": plan["artifact_id"],
            "artifact_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "version": plan["version"],
        }
        try:
            self.approval_service.require_approved(
                project_id, "model_approval", canonical_hash(payload)
            )
        except ValueError as error:
            raise ValueError("Required model approval does not match current content") from error

    def _require_experiment_results(self, project_id: str) -> None:
        experiments = [
            item for item in self.store.list_experiments(project_id)
            if item["status"] == "completed"
        ]
        kinds = {item["config"]["model"]["kind"] for item in experiments}
        if "baseline" not in kinds or not any(kind != "baseline" for kind in kinds):
            raise ValueError("Result validation requires completed baseline and candidate experiments")
        root = Path(self.store.get_project(project_id)["workspace_path"]).resolve()
        for experiment in experiments:
            metrics_path = root / "experiments" / experiment["experiment_id"] / "metrics.json"
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ValueError("Result validation requires validation metrics") from error
            try:
                validated = [MetricRecord.model_validate(item) for item in metrics]
            except Exception as error:
                raise ValueError("Result validation requires validation metrics") from error
            if not validated or not any(item.split == "validation" for item in validated):
                raise ValueError("Result validation requires validation metrics")
        artifacts = self.store.list_artifacts(project_id)
        if not any(item["artifact_type"] in {"experiment_figure", "experiment_table"} for item in artifacts):
            raise ValueError("Result validation requires a registered figure or table")
