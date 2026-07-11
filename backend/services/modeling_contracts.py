from pydantic import BaseModel, ConfigDict, Field


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


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProblemSpec(StrictModel):
    title: str
    subproblems: list[str]
    objectives: list[str]
    constraints: list[str]
    evaluation_requirements: list[str]
    deliverables: list[str]


class ModelCandidate(StrictModel):
    name: str
    assumptions: list[str]
    features: list[str]
    algorithm: str
    metrics: list[str]
    risks: list[str]


class ModelPlan(StrictModel):
    problem_summary: str
    candidates: list[ModelCandidate] = Field(min_length=1, max_length=3)
