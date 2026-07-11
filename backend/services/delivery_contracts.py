from pydantic import BaseModel


class DeliveryFile(BaseModel):
    relative_path: str
    sha256: str
    size: int
    role: str
    included_in_git: bool
    exclusion_reason: str | None = None


class ReproductionIssue(BaseModel):
    code: str
    message: str
    blocking: bool


class ReproductionCheck(BaseModel):
    ok: bool
    issues: list[ReproductionIssue]


class DeliveryManifest(BaseModel):
    project_id: str
    generated_at: str
    reproduction_command: list[str]
    files: list[DeliveryFile]
    experiment_ids: list[str]
    paper_claim_count: int
