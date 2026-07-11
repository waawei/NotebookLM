from pydantic import BaseModel


class ModelingArtifact(BaseModel):
    artifact_id: str
    project_id: str
    artifact_type: str
    relative_path: str
    sha256: str
    source_run_id: str | None = None
    source_experiment_id: str | None = None
    version: int
    created_at: str
