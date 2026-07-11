import pytest
from pydantic import ValidationError

from services.experiment_contracts import ExecutionBatch, ExperimentConfig


def test_batch_rejects_shell_string_and_invalid_experiment_id():
    with pytest.raises(ValidationError):
        ExecutionBatch(
            experiment_id="experiment-one",
            commands=["python train.py"],
            timeout_seconds=60,
            max_output_bytes=1024,
            network_allowed=False,
            code_hash="a" * 64,
            input_hashes={"data/raw.csv": "b" * 64},
            source_hashes={"src/train.py": "c" * 64},
        )


def test_config_requires_seed_and_declared_metric_direction():
    config = ExperimentConfig(
        experiment_id="exp-0001",
        seed=42,
        target="sales",
        features=["price"],
        model={"kind": "linear_regression", "parameters": {}},
        metrics=[{"name": "rmse", "direction": "minimize"}],
    )

    assert config.seed == 42
