import asyncio
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess

from fakes.fake_modeling_llm import BASELINE_FILES, CANDIDATE_FILES, FakeModelingLLM, RESPONSES
from services.modeling_code_agent_service import GeneratedExperiment


ROOT = Path(__file__).parent / "fixtures" / "modeling_competition"


def test_competition_fixture_has_exact_contract_and_24_rows():
    with (ROOT / "train.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    contract = json.loads((ROOT / "expected_contracts.json").read_text(encoding="utf-8"))

    assert len(rows) == 24
    assert rows == [
        {"price": price, "promotion": promotion, "weekday": weekday, "sales": sales}
        for price, promotion, weekday, sales in [
            ("10", "0", "1", "105"), ("11", "0", "2", "101"), ("12", "0", "3", "98"),
            ("13", "0", "4", "94"), ("14", "0", "5", "91"), ("15", "0", "6", "88"),
            ("16", "0", "7", "86"), ("10", "1", "1", "124"), ("11", "1", "2", "121"),
            ("12", "1", "3", "118"), ("13", "1", "4", "115"), ("14", "1", "5", "112"),
            ("15", "1", "6", "109"), ("16", "1", "7", "106"), ("9", "0", "1", "108"),
            ("9", "1", "2", "129"), ("17", "0", "3", "82"), ("17", "1", "4", "102"),
            ("12", "0", "5", "96"), ("12", "1", "6", "116"), ("14", "0", "7", "89"),
            ("14", "1", "1", "114"), ("11", "0", "4", "100"), ("15", "1", "5", "110"),
        ]
    ]
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


def test_fixture_generated_files_execute_declared_pipeline_and_candidate_registers_figure(tmp_path):
    fake = FakeModelingLLM()
    expected_paths = {
        "src/prepare.py",
        "src/features.py",
        "src/train.py",
        "src/evaluate.py",
        "src/visualize.py",
        "tests/test_pipeline.py",
        "requirements.txt",
    }
    for candidate, expected_files, expects_figure in (
        ("mean_baseline", BASELINE_FILES, False),
        ("linear_regression", CANDIDATE_FILES, True),
    ):
        project = tmp_path / ("candidate" if expects_figure else "baseline")
        payload = json.loads(asyncio.run(fake.generate(f"STAGE:programmer candidate {candidate}")))
        generated = GeneratedExperiment.model_validate(payload)
        files = {file.path: file.content for file in generated.files}

        assert set(files) == expected_paths
        assert files == expected_files
        assert "train_test_split(frame, test_size=0.25, random_state=42)" in files["src/train.py"]
        shutil.copytree(ROOT, project / "data" / "raw", dirs_exist_ok=True)
        (project / "data" / "raw" / "problem.txt").unlink(missing_ok=True)
        for relative, content in files.items():
            path = project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        (project / "experiments" / "exp-0001").mkdir(parents=True)
        environment = {**os.environ, "PYTHONPATH": str(project)}
        for command in generated.commands:
            assert command[0] == "python"
            subprocess.run(command, cwd=project, env=environment, check=True)
        metrics = json.loads((project / "experiments" / "exp-0001" / "metrics.json").read_text(encoding="utf-8"))
        assert metrics == [
            {"name": "rmse", "value": metrics[0]["value"], "split": "validation"},
            {"name": "mae", "value": metrics[1]["value"], "split": "validation"},
        ]
        assert (project / "experiments" / "exp-0001" / "figures" / "prediction.png").exists() is expects_figure
        artifacts = json.loads((project / "experiments" / "exp-0001" / "artifacts.json").read_text(encoding="utf-8"))
        assert artifacts == (["experiments/exp-0001/figures/prediction.png"] if expects_figure else [])
