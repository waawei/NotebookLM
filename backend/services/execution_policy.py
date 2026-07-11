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
            if command[1:4] == ["-m", "pip", "install"]:
                if command != install_command:
                    raise ValueError("pip command must use the approved dependency installation form")
                if not batch.network_allowed:
                    raise ValueError("Dependency installation requires network_allowed: true")
                continue
            if command[1:3] == ["-m", "pip"]:
                raise ValueError("pip command must use the approved dependency installation form")
            for argument in command[1:]:
                self._validate_path_argument(root, argument)

    @staticmethod
    def _validate_path_argument(root: Path, argument: str) -> None:
        if argument.startswith("-"):
            return
        normalized = argument.replace("\\", "/")
        if "/" not in normalized and not normalized.endswith(".py"):
            return
        path = Path(normalized)
        resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
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
