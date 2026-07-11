import hashlib
from pathlib import Path, PurePosixPath

from services.modeling_contracts import ModelingArtifact


class ArtifactService:
    def __init__(self, store):
        self.store = store

    def register(
        self,
        project_id: str,
        artifact_type: str,
        relative_path: str,
        source_run_id: str | None = None,
        source_experiment_id: str | None = None,
    ) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        normalized = PurePosixPath(relative_path.replace("\\", "/")).as_posix()
        root = Path(project["workspace_path"]).resolve()
        target = (root / normalized).resolve()
        if target == root or root not in target.parents:
            raise ValueError("Artifact path is outside project workspace")
        if not target.is_file():
            raise ValueError("Artifact file does not exist")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        versions = [
            item["version"]
            for item in self.store.list_artifacts(project_id)
            if item["relative_path"] == normalized
        ]
        artifact = self.store.create_artifact(
            project_id,
            artifact_type,
            normalized,
            digest,
            source_run_id,
            source_experiment_id,
            max(versions, default=0) + 1,
        )
        return ModelingArtifact.model_validate(artifact).model_dump()

    def resolve(self, project_id: str, artifact_id: str) -> dict:
        artifact = self.store.get_artifact(artifact_id)
        if not artifact or artifact["project_id"] != project_id:
            raise ValueError("Artifact not found")
        return ModelingArtifact.model_validate(artifact).model_dump()

    def list_for_project(self, project_id: str) -> list[dict]:
        return [
            ModelingArtifact.model_validate(item).model_dump()
            for item in self.store.list_artifacts(project_id)
        ]

    def remove(self, project_id: str, artifact_id: str) -> None:
        self.resolve(project_id, artifact_id)
        self.store.delete_artifact(artifact_id)
