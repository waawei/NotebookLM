import json
import re


RESPONSES = {
    "problem_parser": {"title": "Sales forecasting", "subproblems": ["Build a baseline", "Build a regression model", "Compare validation metrics"], "objectives": ["Predict sales"], "constraints": ["Use a deterministic split"], "evaluation_requirements": ["validation RMSE", "validation MAE"], "deliverables": ["code", "prediction figure", "paper PDF"]},
    "model_planner": {"problem_summary": "Predict sales from price, promotion, and weekday.", "candidates": [{"name": "mean_baseline", "assumptions": ["validation target is unseen"], "features": ["price", "promotion", "weekday"], "algorithm": "training-target mean", "metrics": ["rmse", "mae"], "risks": ["underfitting"]}, {"name": "linear_regression", "assumptions": ["effects are approximately additive"], "features": ["price", "promotion", "weekday"], "algorithm": "linear regression", "metrics": ["rmse", "mae"], "risks": ["nonlinear effects"]}]},
    "paper_writer": {"markdown": "# Sales Forecasting\n\n## Problem\nWe compare two models.\n\n## Results\nValidation RMSE is {{metric:exp-0002.validation_rmse}} and MAE is {{metric:exp-0002.validation_mae}}. Figure: {{figure:artifact-prediction}}.\n\n## Limitations\nThe fixture is small and synthetic.\n", "latex": "\\documentclass{article}\n\\begin{document}\n\\section{Sales Forecasting}\nValidation RMSE is {{metric:exp-0002.validation_rmse}} and MAE is {{metric:exp-0002.validation_mae}}.\\end{document}\n"},
    "reviewer": {"issues": []},
}

_PREPARE = """import pandas as pd\n\ndef load():\n    return pd.read_csv('data/raw/train.csv')\n"""
_FEATURES = """FEATURES = ['price', 'promotion', 'weekday']\nTARGET = 'sales'\n"""
_EVALUATE = """import json\nfrom sklearn.metrics import mean_absolute_error, mean_squared_error\n\ndef write_metrics(actual, predicted):\n    with open('metrics.json', 'w', encoding='utf-8') as handle:\n        json.dump({'validation_rmse': mean_squared_error(actual, predicted) ** 0.5, 'validation_mae': mean_absolute_error(actual, predicted)}, handle)\n"""
_VISUALIZE = """import matplotlib.pyplot as plt\n\ndef plot(actual, predicted):\n    plt.scatter(actual, predicted)\n    plt.xlabel('actual')\n    plt.ylabel('predicted')\n    plt.savefig('figures/prediction.png')\n"""
_TEST = """from src.train import run\n\ndef test_pipeline():\n    result = run()\n    assert set(result) == {'validation_rmse', 'validation_mae'}\n"""
_REQUIREMENTS = "pandas==2.2.2\nscikit-learn==1.5.1\nmatplotlib==3.9.1\n"
_BASELINE_TRAIN = """import json\nfrom sklearn.model_selection import train_test_split\nfrom src.prepare import load\nfrom src.evaluate import write_metrics\n\ndef run():\n    frame = load()\n    train, validation = train_test_split(frame, test_size=0.25, random_state=42)\n    predicted = [train.sales.mean()] * len(validation)\n    write_metrics(validation.sales, predicted)\n    return json.load(open('metrics.json', encoding='utf-8'))\n\nif __name__ == '__main__': run()\n"""
_CANDIDATE_TRAIN = """import json, os\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\nfrom src.prepare import load\nfrom src.features import FEATURES, TARGET\nfrom src.evaluate import write_metrics\nfrom src.visualize import plot\n\ndef run():\n    frame = load()\n    train, validation = train_test_split(frame, test_size=0.25, random_state=42)\n    model = LinearRegression().fit(train[FEATURES], train[TARGET])\n    predicted = model.predict(validation[FEATURES])\n    write_metrics(validation[TARGET], predicted)\n    os.makedirs('figures', exist_ok=True)\n    plot(validation[TARGET], predicted)\n    json.dump([{'artifact_id': 'artifact-prediction', 'type': 'figure', 'path': 'figures/prediction.png'}], open('artifacts.json', 'w', encoding='utf-8'))\n    return json.load(open('metrics.json', encoding='utf-8'))\n\nif __name__ == '__main__': run()\n"""

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
        raise AssertionError("Prompt did not declare a known modeling stage")
