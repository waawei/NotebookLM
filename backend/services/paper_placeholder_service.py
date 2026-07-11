import json
import re
from decimal import Decimal
from pathlib import Path


TOKEN = re.compile(r"\{\{(metric|figure|table):([^}]+)\}\}")


class PaperPlaceholderService:
    def __init__(self, store, artifact_service):
        self.store = store
        self.artifacts = artifact_service

    def resolve_markdown(self, project_id: str, markdown: str) -> tuple[str, list[dict]]:
        claims = []

        def replace(match: re.Match) -> str:
            kind, reference = match.group(1), match.group(2)
            if kind == "metric":
                try:
                    experiment_id, metric_name = reference.split(".", 1)
                except ValueError as error:
                    raise ValueError("Unresolvable paper placeholder") from error
                experiment = self.store.get_experiment(experiment_id)
                if (
                    not experiment
                    or experiment["project_id"] != project_id
                    or experiment["status"] != "completed"
                ):
                    raise ValueError("Unresolvable paper placeholder")
                artifact = next(
                    (
                        item for item in self.store.list_artifacts(project_id)
                        if item["source_experiment_id"] == experiment_id
                        and item["artifact_type"] == "experiment_metrics"
                    ),
                    None,
                )
                if not artifact:
                    raise ValueError("Unresolvable paper placeholder")
                project = self.store.get_project(project_id)
                path = Path(project["workspace_path"]) / artifact["relative_path"]
                try:
                    records = json.loads(path.read_text(encoding="utf-8"))
                    record = next(
                        item for item in records
                        if f"{item['split']}_{item['name']}" == metric_name
                    )
                except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                    raise ValueError("Unresolvable paper placeholder") from error
                value = format(Decimal(str(record["value"])), "f")
                claims.append({
                    "placeholder": match.group(0), "claim_type": kind,
                    "artifact_id": artifact["artifact_id"], "experiment_id": experiment_id,
                    "metric_name": metric_name, "rendered_value": value,
                })
                return value
            try:
                artifact = self.artifacts.resolve(project_id, reference)
            except ValueError as error:
                raise ValueError("Unresolvable paper placeholder") from error
            if (
                artifact["artifact_type"] not in {kind, f"experiment_{kind}"}
                or not artifact["source_experiment_id"]
            ):
                raise ValueError("Unresolvable paper placeholder")
            experiment = self.store.get_experiment(artifact["source_experiment_id"])
            if not experiment or experiment["status"] != "completed":
                raise ValueError("Unresolvable paper placeholder")
            claims.append({
                "placeholder": match.group(0), "claim_type": kind,
                "artifact_id": artifact["artifact_id"],
                "experiment_id": artifact["source_experiment_id"], "metric_name": None,
                "rendered_value": artifact["relative_path"],
            })
            return artifact["relative_path"]

        return TOKEN.sub(replace, markdown), claims
