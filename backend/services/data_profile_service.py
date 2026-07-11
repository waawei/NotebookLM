import json
from pathlib import Path

import pandas as pd


class DataProfileService:
    def __init__(self, store, artifact_service):
        self.store = store
        self.artifact_service = artifact_service

    def profile(self, project_id: str, artifact_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        artifact = self.artifact_service.resolve(project_id, artifact_id)
        if artifact["artifact_type"] != "data_input":
            raise ValueError("Artifact must be a CSV data input")
        source = Path(project["workspace_path"]) / artifact["relative_path"]
        frame = pd.read_csv(source)

        columns = {}
        for name in frame.columns:
            series = frame[name]
            item = {
                "dtype": str(series.dtype),
                "missing": int(series.isna().sum()),
                "unique": int(series.nunique(dropna=True)),
            }
            if pd.api.types.is_numeric_dtype(series) and not series.dropna().empty:
                clean = series.dropna()
                item["numeric"] = {
                    "min": float(clean.min()),
                    "max": float(clean.max()),
                    "mean": float(clean.mean()),
                    "std": float(clean.std(ddof=0)),
                }
            columns[str(name)] = item

        result = {
            "source_artifact_id": artifact_id,
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "duplicate_rows": int(frame.duplicated().sum()),
            "columns": columns,
        }
        analysis = Path(project["workspace_path"]) / "analysis"
        profile_path = analysis / "data_profile.json"
        report_path = analysis / "data_report.md"
        profile_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        lines = [
            "# Data Profile",
            "",
            f"Source artifact: {artifact_id}",
            f"Rows: {result['row_count']}",
            f"Columns: {result['column_count']}",
            f"Duplicate rows: {result['duplicate_rows']}",
            "",
            "## Columns",
        ]
        for name, item in columns.items():
            lines.append(
                f"- {name}: dtype={item['dtype']}, missing={item['missing']}, unique={item['unique']}"
            )
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.artifact_service.register(
            project_id, "data_profile", "analysis/data_profile.json"
        )
        self.artifact_service.register(
            project_id, "data_report", "analysis/data_report.md"
        )
        return result
