import hashlib
import json
import os
import tempfile
from pathlib import Path, PurePosixPath

from pydantic import Field, ValidationError, field_validator, model_validator

from services.approval_service import canonical_hash
from services.experiment_contracts import ExecutionBatch, ExperimentConfig
from services.modeling_contracts import StrictModel


class GeneratedFile(StrictModel):
    path: str
    content: str = Field(max_length=200_000)

    @field_validator("path")
    @classmethod
    def allowed_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        allowed = {
            "src/prepare.py",
            "src/features.py",
            "src/train.py",
            "src/evaluate.py",
            "src/visualize.py",
            "tests/test_pipeline.py",
            "requirements.txt",
        }
        if path.as_posix() not in allowed:
            raise ValueError("Generated file is not an allowed source path")
        return path.as_posix()


class GeneratedExperiment(StrictModel):
    files: list[GeneratedFile] = Field(min_length=1)
    commands: list[list[str]] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_pipeline(self):
        paths = {file.path for file in self.files}
        if "tests/test_pipeline.py" not in paths:
            raise ValueError("Generated experiment requires a pipeline test")
        if "requirements.txt" not in paths:
            raise ValueError("Generated experiment requires requirements.txt")
        if not any(path.startswith("src/") for path in paths):
            raise ValueError("Generated experiment requires source files")
        return self


class ModelingCodeAgentService:
    def __init__(self, store, artifact_service, approval_service, run_service, llm):
        self.store = store
        self.artifact_service = artifact_service
        self.approval_service = approval_service
        self.run_service = run_service
        self.llm = llm

    async def prepare_experiment(self, project_id: str, candidate_index: int) -> dict:
        project = self._project(project_id)
        plan, plan_payload = self._approved_plan(project)
        candidates = plan_payload.get("candidates")
        if not isinstance(candidates, list) or not 0 <= candidate_index < len(candidates):
            raise ValueError("Approved model plan candidate is unavailable")
        candidate = candidates[candidate_index]
        experiment_id = self._next_experiment_id(project)
        prompt = (
            "Return only JSON matching the supplied generated experiment schema. "
            "Use deterministic seeds, train-validation separation, machine-readable metrics, "
            "and project-relative paths.\n"
            + json.dumps(GeneratedExperiment.model_json_schema(), ensure_ascii=False)
            + "\nApproved model candidate:\n"
            + json.dumps(candidate, ensure_ascii=False)
        )
        try:
            generated = GeneratedExperiment.model_validate_json(await self.llm.generate(prompt))
        except (ValidationError, json.JSONDecodeError) as error:
            raise ValueError(self._validation_message(error)) from error
        self._validate_commands(generated.commands)
        root = Path(project["workspace_path"]).resolve()
        config = self._config(experiment_id, candidate, plan_payload)
        input_hashes = self._input_hashes(project)
        source_hashes = self._source_hashes(
            generated.files,
            f"experiments/{experiment_id}/config.json",
            json.dumps(config, ensure_ascii=False, sort_keys=True),
        )
        source_hash = self._combined_hash(source_hashes)
        batch = ExecutionBatch(
            experiment_id=experiment_id,
            commands=generated.commands,
            timeout_seconds=600,
            max_output_bytes=1_048_576,
            network_allowed=False,
            code_hash=source_hash,
            input_hashes=input_hashes,
            source_hashes=source_hashes,
        )
        task, run = self.run_service.start(
            project_id,
            "experiment_implementation",
            "programming",
            "modeling_programmer",
            {"candidate_index": candidate_index, "model_plan_artifact_id": plan["artifact_id"]},
            ["src", "tests/test_pipeline.py", f"experiments/{experiment_id}/config.json"],
        )
        paths = {root / file.path: file.content.encode("utf-8") for file in generated.files}
        paths[root / "experiments" / experiment_id / "config.json"] = (
            json.dumps(config, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        paths[root / "reproduce.ps1"] = self._reproduce(experiment_id).encode("utf-8")
        paths[root / "README.md"] = (
            "# Modeling Project\n\nRun `powershell -ExecutionPolicy Bypass -File reproduce.ps1` from this directory.\n"
        ).encode("utf-8")
        previous = {path: path.read_bytes() if path.exists() else None for path in paths}
        try:
            for path, content in paths.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                self._atomic_write(path, content)
            experiment = self.store.create_experiment(experiment_id, project_id, config, None)
            self.store.set_experiment_execution_batch(
                experiment_id,
                canonical_hash(batch.model_dump(mode="json")),
                batch.model_dump(mode="json"),
            )
            experiment = self.store.get_experiment(experiment_id)
            self.run_service.complete(task["task_id"], run["run_id"], [])
            return {"experiment": experiment, "batch": batch.model_dump(mode="json")}
        except Exception as error:
            for path, content in previous.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    self._atomic_write(path, content)
            current = self.store.get_task(task["task_id"])
            if current and current["status"] == "running":
                self.run_service.fail(task, run["run_id"], "Experiment preparation failed")
            raise ValueError("Experiment preparation failed") from error

    def _approved_plan(self, project: dict) -> tuple[dict, dict]:
        plans = [
            artifact
            for artifact in self.store.list_artifacts(project["project_id"])
            if artifact["artifact_type"] == "model_plan"
        ]
        if not plans:
            raise ValueError("Approved model plan is required")
        plan = max(plans, key=lambda item: (item["created_at"], item["artifact_id"]))
        root = Path(project["workspace_path"]).resolve()
        target = (root / plan["relative_path"]).resolve()
        if target == root or root not in target.parents or not target.is_file():
            raise ValueError("Approved model plan is unavailable")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        payload = {"artifact_id": plan["artifact_id"], "artifact_sha256": digest, "version": plan["version"]}
        self.approval_service.require_approved(project["project_id"], "model_approval", canonical_hash(payload))
        return plan, json.loads(target.read_text(encoding="utf-8"))

    def _input_hashes(self, project: dict) -> dict[str, str]:
        root = Path(project["workspace_path"]).resolve()
        hashes = {}
        for artifact in self.store.list_artifacts(project["project_id"]):
            if artifact["artifact_type"] not in {"data_input", "data_profile", "model_plan"}:
                continue
            path = (root / artifact["relative_path"]).resolve()
            if path == root or root not in path.parents or not path.is_file():
                raise ValueError("Experiment input is unavailable")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != artifact["sha256"]:
                raise ValueError("Experiment input hash does not match registered artifact")
            hashes[artifact["relative_path"]] = digest
        return hashes

    @staticmethod
    def _source_hashes(
        files: list[GeneratedFile], config_path: str, config_content: str
    ) -> dict[str, str]:
        content = {file.path: file.content for file in files}
        content[config_path] = config_content
        return {
            path: hashlib.sha256(value.encode("utf-8")).hexdigest()
            for path, value in content.items()
        }

    @staticmethod
    def _combined_hash(source_hashes: dict[str, str]) -> str:
        digest = hashlib.sha256()
        for path, value in sorted(source_hashes.items()):
            digest.update(path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(value.encode("ascii"))
            digest.update(b"\0")
        return digest.hexdigest()

    def _next_experiment_id(self, project: dict) -> str:
        existing = {item["experiment_id"] for item in self.store.list_experiments(project["project_id"])}
        number = 1
        while f"exp-{number:04d}" in existing:
            number += 1
        return f"exp-{number:04d}"

    @staticmethod
    def _validate_commands(commands: list[list[str]]) -> None:
        for command in commands:
            if not command or any(not isinstance(item, str) or not item for item in command):
                raise ValueError("Generated command must be a non-empty argument array")
            if command[0] != "python":
                raise ValueError("Generated commands must begin with python")
            if any(Path(argument).is_absolute() or ".." in PurePosixPath(argument).parts for argument in command[1:]):
                raise ValueError("Generated command path escapes project workspace")

    @staticmethod
    def _config(experiment_id: str, candidate: dict, plan: dict) -> dict:
        features = candidate.get("features") or ["feature"]
        metrics = candidate.get("metrics") or ["rmse"]
        return ExperimentConfig(
            experiment_id=experiment_id,
            seed=42,
            target="target",
            features=[str(feature) for feature in features],
            model={
                "kind": "baseline" if candidate.get("name", "").lower().startswith("baseline") else str(candidate.get("algorithm", "candidate")),
                "parameters": {},
            },
            metrics=[
                {"name": str(metric), "direction": "maximize" if str(metric).lower() in {"accuracy", "f1", "r2"} else "minimize"}
                for metric in metrics
            ],
        ).model_dump(mode="json")

    @staticmethod
    def _reproduce(experiment_id: str) -> str:
        return "\n".join([
            "$ErrorActionPreference = 'Stop'",
            "& .\\.venv\\Scripts\\python.exe -m pytest tests",
            f"& .\\.venv\\Scripts\\python.exe src\\prepare.py --config experiments\\{experiment_id}\\config.json",
            f"& .\\.venv\\Scripts\\python.exe src\\train.py --config experiments\\{experiment_id}\\config.json",
            f"& .\\.venv\\Scripts\\python.exe src\\evaluate.py --experiment {experiment_id}",
        ]) + "\n"

    def _project(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        return project

    @staticmethod
    def _validation_message(error: Exception) -> str:
        if isinstance(error, json.JSONDecodeError):
            return "Generated experiment is not valid JSON"
        return "; ".join(item["msg"] for item in error.errors(include_input=False))

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
