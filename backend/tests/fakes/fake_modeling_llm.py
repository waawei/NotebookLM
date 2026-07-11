import json
import re


RESPONSES = {
    "problem_parser": {"title": "Sales forecasting", "subproblems": ["Build a baseline", "Build a regression model", "Compare validation metrics"], "objectives": ["Predict sales"], "constraints": ["Use a deterministic split"], "evaluation_requirements": ["validation RMSE", "validation MAE"], "deliverables": ["code", "prediction figure", "paper PDF"]},
    "model_planner": {"problem_summary": "Predict sales from price, promotion, and weekday.", "candidates": [{"name": "mean_baseline", "assumptions": ["validation target is unseen"], "features": ["price", "promotion", "weekday"], "algorithm": "training-target mean", "metrics": ["rmse", "mae"], "risks": ["underfitting"]}, {"name": "linear_regression", "assumptions": ["effects are approximately additive"], "features": ["price", "promotion", "weekday"], "algorithm": "linear regression", "metrics": ["rmse", "mae"], "risks": ["nonlinear effects"]}]},
    "paper_writer": {"markdown": "# Sales Forecasting\n\n## Subproblem 1\nBuild and compare the baseline and regression models.\n\n## Results\nValidation RMSE is {{metric:exp-0002.validation_rmse}} and MAE is {{metric:exp-0002.validation_mae}}. Figure: {{figure:artifact-prediction}}.\n\n## Limitations\nThe fixture is small and synthetic.\n", "latex": "\\documentclass{article}\n\\begin{document}\n\\section{Sales Forecasting}\nValidation RMSE is {{metric:exp-0002.validation_rmse}} and MAE is {{metric:exp-0002.validation_mae}}.\\end{document}\n"},
    "reviewer": {"issues": []},
}

_PREPARE = """import csv
import random

def load():
    with open('data/raw/train.csv', newline='', encoding='utf-8') as handle:
        return [{key: float(value) for key, value in row.items()} for row in csv.DictReader(handle)]

def train_test_split(frame, test_size=0.25, random_state=42):
    shuffled = list(frame); random.Random(random_state).shuffle(shuffled)
    validation_count = max(1, round(len(shuffled) * test_size))
    return shuffled[validation_count:], shuffled[:validation_count]
"""
_FEATURES = """FEATURES = ['price', 'promotion', 'weekday']
TARGET = 'sales'
"""
_EVALUATE = """import json
from pathlib import Path

def experiment_dir():
    return max(Path('experiments').glob('exp-*'))

def write_metrics(actual, predicted):
    errors = [observed - estimate for observed, estimate in zip(actual, predicted)]
    values = [{'name': 'rmse', 'value': (sum(error * error for error in errors) / len(errors)) ** 0.5, 'split': 'validation'}, {'name': 'mae', 'value': sum(abs(error) for error in errors) / len(errors), 'split': 'validation'}]
    (experiment_dir() / 'metrics.json').write_text(json.dumps(values), encoding='utf-8')
    return values
"""
_VISUALIZE = """import base64

def plot(actual, predicted, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL9AwAAAABJRU5ErkJggg=='))
"""
_TEST = """from src.train import run

def test_pipeline():
    result = run()
    assert set(result) == {'validation_rmse', 'validation_mae'}
"""
_REQUIREMENTS = "# Uses the Python standard library only.\n"
_BASELINE_TRAIN = """from src.prepare import load, train_test_split
from src.evaluate import experiment_dir, write_metrics
from src.features import TARGET

def run():
    frame = load(); train, validation = train_test_split(frame, test_size=0.25, random_state=42)
    mean = sum(row[TARGET] for row in train) / len(train)
    values = write_metrics([row[TARGET] for row in validation], [mean] * len(validation))
    (experiment_dir() / 'artifacts.json').write_text('[]', encoding='utf-8')
    return {'validation_rmse': values[0]['value'], 'validation_mae': values[1]['value']}

if __name__ == '__main__': run()
"""
_CANDIDATE_TRAIN = """import json
from src.prepare import load, train_test_split
from src.features import FEATURES, TARGET
from src.evaluate import experiment_dir, write_metrics
from src.visualize import plot

def _solve(matrix):
    size = len(matrix)
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(matrix[row][column]))
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        divisor = matrix[column][column]
        matrix[column] = [value / divisor for value in matrix[column]]
        for row in range(size):
            if row != column:
                factor = matrix[row][column]
                matrix[row] = [value - factor * pivot_value for value, pivot_value in zip(matrix[row], matrix[column])]
    return [row[-1] for row in matrix]

def _fit(rows):
    vectors = [[1.0, *(row[name] for name in FEATURES)] for row in rows]
    width = len(vectors[0])
    return _solve([[sum(vector[row_index] * vector[column_index] for vector in vectors) for column_index in range(width)] + [sum(vector[row_index] * row[TARGET] for vector, row in zip(vectors, rows))] for row_index in range(width)])

def run():
    frame = load(); train, validation = train_test_split(frame, test_size=0.25, random_state=42)
    coefficients = _fit(train)
    predicted = [sum(weight * value for weight, value in zip(coefficients, [1.0, *(row[name] for name in FEATURES)])) for row in validation]
    values = write_metrics([row[TARGET] for row in validation], predicted); directory = experiment_dir(); figure = directory / 'figures' / 'prediction.png'
    plot([row[TARGET] for row in validation], predicted, figure)
    (directory / 'artifacts.json').write_text(json.dumps([figure.as_posix()]), encoding='utf-8')
    return {'validation_rmse': values[0]['value'], 'validation_mae': values[1]['value']}

if __name__ == '__main__': run()
"""

BASELINE_FILES = {"src/prepare.py": _PREPARE, "src/features.py": _FEATURES, "src/train.py": _BASELINE_TRAIN, "src/evaluate.py": _EVALUATE, "src/visualize.py": _VISUALIZE, "tests/test_pipeline.py": _TEST, "requirements.txt": _REQUIREMENTS}
CANDIDATE_FILES = {"src/prepare.py": _PREPARE, "src/features.py": _FEATURES, "src/train.py": _CANDIDATE_TRAIN, "src/evaluate.py": _EVALUATE, "src/visualize.py": _VISUALIZE, "tests/test_pipeline.py": _TEST, "requirements.txt": _REQUIREMENTS}


class FakeModelingLLM:
    def __init__(self, responses: dict[str, dict] = RESPONSES):
        self.responses = responses
        self.stage = ""

    async def generate(self, prompt: str) -> str:
        for stage, payload in self.responses.items():
            if f"STAGE:{stage}" in prompt:
                rendered = json.loads(json.dumps(payload, ensure_ascii=False))
                if stage == "paper_writer":
                    match = re.search(r"PREDICTION_ARTIFACT_ID:([A-Za-z0-9-]+)", prompt)
                    if not match:
                        raise AssertionError("Paper prompt omitted prediction artifact ID")
                    rendered["markdown"] = rendered["markdown"].replace("artifact-prediction", match.group(1))
                return json.dumps(rendered, ensure_ascii=False)
        if "STAGE:programmer" in prompt:
            files = BASELINE_FILES if "mean_baseline" in prompt else CANDIDATE_FILES
            return json.dumps({"files": [{"path": path, "content": content} for path, content in files.items()], "commands": [["python", "-m", "pytest", "tests/test_pipeline.py"], ["python", "src/train.py"]]}, ensure_ascii=False)
        raise AssertionError("Prompt did not declare a known modeling stage")
