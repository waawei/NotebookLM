import hashlib
import json
import math
import os
import tempfile
import warnings
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
        root = Path(project["workspace_path"]).resolve()
        source = (root / artifact["relative_path"]).resolve()
        if source == root or root not in source.parents:
            raise ValueError("CSV data input is outside project workspace")
        if source.suffix.lower() != ".csv":
            raise ValueError("Artifact must be a CSV data input")
        if not source.is_file():
            raise ValueError("CSV data input does not exist")
        if hashlib.sha256(source.read_bytes()).hexdigest() != artifact["sha256"]:
            raise ValueError("CSV data input hash does not match registered artifact")
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
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    item["numeric"] = {
                        "min": self._finite_or_none(clean.min()),
                        "max": self._finite_or_none(clean.max()),
                        "mean": self._finite_or_none(clean.mean()),
                        "std": self._finite_or_none(clean.std(ddof=0)),
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
        profile_bytes = (
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        ).encode("utf-8")
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
        report_bytes = ("\n".join(lines) + "\n").encode("utf-8")
        previous = {
            profile_path: profile_path.read_bytes() if profile_path.exists() else None,
            report_path: report_path.read_bytes() if report_path.exists() else None,
        }
        registered = []
        try:
            self._atomic_write(profile_path, profile_bytes)
            self._atomic_write(report_path, report_bytes)
            registered.append(
                self.artifact_service.register(
                    project_id, "data_profile", "analysis/data_profile.json"
                )
            )
            registered.append(
                self.artifact_service.register(
                    project_id, "data_report", "analysis/data_report.md"
                )
            )
            return result
        except Exception:
            for created in reversed(registered):
                self.artifact_service.remove(project_id, created["artifact_id"])
            for path, content in previous.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    self._atomic_write(path, content)
            raise

    @staticmethod
    def _finite_or_none(value) -> float | None:
        number = float(value)
        return number if math.isfinite(number) else None

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
