import hashlib
from pathlib import Path

from services.approval_service import canonical_hash


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
            return

        plans = [item for item in artifacts if item["artifact_type"] == "model_plan"]
        if not plans:
            raise ValueError("Missing required model plan artifact")
        plan = max(plans, key=lambda item: (item["version"], item["created_at"]))
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
