import re

from services.document_metadata_store import DocumentMetadataStore
from services.modeling_state import next_state, previous_state


class ModelingProjectService:
    def __init__(self, store, workspace_service, agent_store=None):
        self.store = store
        self.workspace_service = workspace_service
        self.agent_store = agent_store or DocumentMetadataStore()

    @staticmethod
    def _slug(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return slug or "modeling-project"

    def create_project(self, name: str, deadline: str | None = None) -> dict:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Project name is required")
        slug = self._slug(clean_name)
        path = self.workspace_service.create(slug)
        try:
            return self.store.create_project(clean_name, slug, str(path), deadline)
        except Exception:
            self.workspace_service.remove_created(path)
            raise

    def list_projects(self) -> list[dict]:
        return self.store.list_projects()

    def get_project(self, project_id: str) -> dict | None:
        return self.store.get_project(project_id)

    def list_tasks(self, project_id: str) -> list[dict]:
        self._require(project_id)
        return self.store.list_tasks(project_id)

    def list_runs(self, project_id: str) -> list[dict]:
        self._require(project_id)
        return self.agent_store.list_agent_runs(project_id=project_id)

    def advance(self, project_id: str) -> dict:
        project = self._require(project_id)
        target = next_state(project["state"])
        self.store.transition_state(project_id, project["state"], target, "advance")
        return self._require(project_id)

    def rollback(self, project_id: str, reason: str | None) -> dict:
        project = self._require(project_id)
        target = previous_state(project["state"])
        reason_text = reason.strip() if isinstance(reason, str) else ""
        self.store.transition_state(
            project_id,
            project["state"],
            target,
            reason_text or "rollback",
        )
        return self._require(project_id)

    def _require(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        return project
