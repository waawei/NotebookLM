import os
import tempfile

import pytest

from services.modeling_store import ModelingStore


def test_experiment_record_is_created_once_and_config_is_immutable():
    with tempfile.TemporaryDirectory() as tempdir:
        store = ModelingStore(os.path.join(tempdir, "modeling.db"))
        project = store.create_project("Forecast", "forecast", tempdir, None)
        config = {
            "experiment_id": "exp-0001",
            "seed": 42,
            "target": "sales",
            "features": ["price"],
            "model": {"kind": "baseline", "parameters": {}},
            "metrics": [{"name": "rmse", "direction": "minimize"}],
        }

        created = store.create_experiment(
            "exp-0001", project["project_id"], config, "a" * 64
        )
        store.update_experiment_status(
            "exp-0001", "running", pid=123, started_at="2026-07-11T00:00:00"
        )

        with pytest.raises(ValueError, match="Experiment already exists"):
            store.create_experiment(
                "exp-0001", project["project_id"], config, "b" * 64
            )

        loaded = store.get_experiment("exp-0001")
        assert created["config"] == config
        assert loaded["config"] == config
        assert loaded["execution_payload_hash"] == "a" * 64
        assert loaded["status"] == "running"
        assert loaded["pid"] == 123


def test_status_update_preserves_omitted_runtime_fields_and_rejects_invalid_config():
    with tempfile.TemporaryDirectory() as tempdir:
        store = ModelingStore(os.path.join(tempdir, "modeling.db"))
        project = store.create_project("Forecast", "forecast", tempdir, None)

        with pytest.raises(ValueError, match="Experiment config is invalid"):
            store.create_experiment("exp-0001", project["project_id"], {"seed": 42}, "a" * 64)

        config = {
            "experiment_id": "exp-0001", "seed": 42, "target": "sales",
            "features": ["price"], "model": {"kind": "baseline", "parameters": {}},
            "metrics": [{"name": "rmse", "direction": "minimize"}],
        }
        store.create_experiment("exp-0001", project["project_id"], config, "a" * 64)
        store.update_experiment_status("exp-0001", "running", started_at="start")
        store.update_experiment_status("exp-0001", "running", pid=123)

        loaded = store.get_experiment("exp-0001")
        assert loaded["started_at"] == "start"
        assert loaded["pid"] == 123
