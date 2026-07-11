from typing import Literal

from pydantic import BaseModel


class PaperClaim(BaseModel):
    placeholder: str
    claim_type: Literal["metric", "figure", "table"]
    artifact_id: str
    experiment_id: str
    metric_name: str | None = None
    rendered_value: str


class ReviewIssue(BaseModel):
    severity: Literal["blocking", "warning", "info"]
    code: str
    message: str
    location: str
    artifact_ids: list[str]
