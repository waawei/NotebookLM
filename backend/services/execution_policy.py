from pathlib import Path

from services.approval_service import canonical_hash
from services.project_environment_service import ProjectEnvironmentService


class ExecutionPolicy:
    def __init__(self, approvals, environment_service=None):
        self.approvals = approvals
        self.environment_service = environment_service or ProjectEnvironmentService()

    def validate_batch(self, project: dict, batch) -> None:
        root = Path(project["workspace_path"]).resolve()
        python_path = self.environment_service.ensure_created(project)
        install_command = self.environment_service.dependency_install_command(project)
        for command in batch.commands:
            if not command or Path(command[0]).resolve() != python_path:
                raise ValueError("Command must use the project virtual environment Python")
            if command == install_command and not batch.network_allowed:
                raise ValueError("Dependency installation requires network_allowed: true")
            for argument in command[1:]:
                path = Path(argument)
                if path.is_absolute():
                    resolved = path.resolve()
                    if resolved != root and root not in resolved.parents:
                        raise ValueError("Command path escapes project workspace")

    def request_execution(self, project: dict, batch) -> dict:
        self.validate_batch(project, batch)
        return self.approvals.request(
            project["project_id"], "execution_approval", batch.model_dump(mode="json")
        )

    def require_execution_approval(self, project: dict, batch) -> dict:
        self.validate_batch(project, batch)
        return self.approvals.require_approved(
            project["project_id"],
            "execution_approval",
            canonical_hash(batch.model_dump(mode="json")),
        )
