from typing import Literal

from pydantic import Field

from services.modeling_contracts import StrictModel


class MetricSpec(StrictModel):
    name: str
    direction: Literal["minimize", "maximize"]


class ModelSpec(StrictModel):
    kind: str
    parameters: dict[str, str | int | float | bool]


class ExperimentConfig(StrictModel):
    experiment_id: str = Field(pattern=r"^exp-[0-9]{4}$")
    seed: int
    target: str
    features: list[str] = Field(min_length=1)
    model: ModelSpec
    metrics: list[MetricSpec] = Field(min_length=1)


class ExecutionBatch(StrictModel):
    experiment_id: str = Field(pattern=r"^exp-[0-9]{4}$")
    commands: list[list[str]] = Field(min_length=1)
    timeout_seconds: int = Field(ge=1, le=3600)
    max_output_bytes: int = Field(ge=1024, le=10_485_760)
    network_allowed: bool = False
    code_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_hashes: dict[str, str]
    source_hashes: dict[str, str] = Field(min_length=1)


class MetricRecord(StrictModel):
    name: str
    value: float
    split: Literal["train", "validation", "test"]
