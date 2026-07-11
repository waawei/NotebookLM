import os
import tempfile

import pytest

from services.modeling_store import ModelingStore


def test_experiment_record_is_created_once_and_config_is_immutable():
    with tempfile.TemporaryDirectory() as tempdir:
        store = ModelingStore(os.path.join(tempdir, "modeling.db"))
        project = store.create_project("Forecast", "forecast", tempdir, None)
        config = {"seed": 42, "model": {"kind": "baseline"}}

        created = store.create_experiment(
            "exp-0001", project["project_id"], config, "payload-hash"
        )
        store.update_experiment_status(
            "exp-0001", "running", pid=123, started_at="2026-07-11T00:00:00"
        )

        with pytest.raises(ValueError, match="Experiment already exists"):
            store.create_experiment(
                "exp-0001", project["project_id"], {"seed": 7}, "changed"
            )

        loaded = store.get_experiment("exp-0001")
        assert created["config"] == config
        assert loaded["config"] == config
        assert loaded["execution_payload_hash"] == "payload-hash"
        assert loaded["status"] == "running"
        assert loaded["pid"] == 123
