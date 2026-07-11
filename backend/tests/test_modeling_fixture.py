import asyncio
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from fakes.fake_modeling_llm import BASELINE_FILES, CANDIDATE_FILES, FakeModelingLLM, RESPONSES


ROOT = Path(__file__).parent / "fixtures" / "modeling_competition"


def test_competition_fixture_has_exact_contract_and_24_rows():
    with (ROOT / "train.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    contract = json.loads((ROOT / "expected_contracts.json").read_text(encoding="utf-8"))

    assert len(rows) == 24
    assert contract == {
        "target": "sales", "features": ["price", "promotion", "weekday"],
        "seed": 42, "candidates": ["mean_baseline", "linear_regression"],
        "validation_metrics": ["rmse", "mae"], "required_artifact_type": "figure", "row_count": 24,
    }


def test_fake_llm_is_stage_keyed_deterministic_and_binds_prediction_artifact():
    fake = FakeModelingLLM(RESPONSES)

    first = json.loads(asyncio.run(fake.generate("STAGE:problem_parser")))
    first["title"] = "mutated"
    second = json.loads(asyncio.run(fake.generate("STAGE:problem_parser")))
    paper = json.loads(asyncio.run(fake.generate("STAGE:paper_writer PREDICTION_ARTIFACT_ID:artifact-123")))

    assert second["title"] == "Sales forecasting"
    assert "artifact-123" in paper["markdown"]


def test_fixture_generated_files_execute_pipeline_and_candidate_registers_figure(tmp_path):
    for files, expects_figure in ((BASELINE_FILES, False), (CANDIDATE_FILES, True)):
        project = tmp_path / ("candidate" if expects_figure else "baseline")
        shutil.copytree(ROOT, project / "data" / "raw", dirs_exist_ok=True)
        (project / "data" / "raw" / "problem.txt").unlink(missing_ok=True)
        for relative, content in files.items():
            path = project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        environment = {**os.environ, "PYTHONPATH": str(project)}
        subprocess.run([sys.executable, "-m", "pytest", "tests/test_pipeline.py", "-q"], cwd=project, env=environment, check=True)
        subprocess.run([sys.executable, "src/train.py"], cwd=project, env=environment, check=True)
        metrics = json.loads((project / "metrics.json").read_text(encoding="utf-8"))
        assert set(metrics) == {"validation_rmse", "validation_mae"}
        assert (project / "figures" / "prediction.png").exists() is expects_figure
