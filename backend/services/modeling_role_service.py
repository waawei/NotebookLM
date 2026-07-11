import hashlib
import json
import os
import tempfile
from pathlib import Path

from PyPDF2 import PdfReader
from pydantic import ValidationError

from services.modeling_contracts import ModelPlan, ProblemSpec


def parse_json_object(text: str) -> dict:
    clean = text.strip()
    if clean.startswith("```json") and clean.endswith("```"):
        clean = clean[7:-3].strip()
    value = json.loads(clean)
    if not isinstance(value, dict):
        raise ValueError("Agent output must be a JSON object")
    return value


class ModelingRoleService:
    def __init__(
        self,
        store,
        artifact_service,
        approval_service,
        run_service,
        llm,
    ):
        self.store = store
        self.artifact_service = artifact_service
        self.approval_service = approval_service
        self.run_service = run_service
        self.llm = llm

    async def parse_problem(self, project_id: str, artifact_id: str) -> dict:
        project = self._project(project_id)
        artifact = self.artifact_service.resolve(project_id, artifact_id)
        if artifact["artifact_type"] != "problem_input":
            raise ValueError("Artifact must be a problem input")
        source = self._validated_file(
            project, artifact, {".pdf", ".md", ".txt"}, "Problem input"
        )
        task, run = self.run_service.start(
            project_id,
            "problem_parsing",
            "modeling",
            "modeling_problem_parser",
            {"artifact_id": artifact_id},
            ["problem/problem_spec.json"],
        )
        output = Path(project["workspace_path"]) / "problem" / "problem_spec.json"
        previous_output = output.read_bytes() if output.exists() else None
        registered = None
        try:
            problem_text = self._read_problem(source)
            prompt = (
                "Return only JSON matching this schema. Do not invent requirements.\n"
                + json.dumps(ProblemSpec.model_json_schema(), ensure_ascii=False)
                + "\nCompetition prompt:\n"
                + problem_text
            )
            model = ProblemSpec.model_validate(parse_json_object(await self.llm.generate(prompt)))
            payload = model.model_dump(mode="json")
            self._atomic_write(
                output,
                (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode(
                    "utf-8"
                ),
            )
            registered = self.artifact_service.register(
                project_id,
                "problem_spec",
                "problem/problem_spec.json",
                source_run_id=run["run_id"],
            )
            self.run_service.complete(
                task["task_id"], run["run_id"], [registered["artifact_id"]]
            )
            return {
                "problem_spec": payload,
                "artifact": registered,
                "task_id": task["task_id"],
                "run_id": run["run_id"],
            }
        except Exception as error:
            if registered:
                self.artifact_service.remove(project_id, registered["artifact_id"])
            self._restore(output, previous_output)
            safe_error = self._safe_error(error)
            current = self.store.get_task(task["task_id"])
            if current and current["status"] == "running":
                self.run_service.fail(task, run["run_id"], safe_error)
            raise ValueError(safe_error) from error

    async def create_model_plan(self, project_id: str, profile_artifact_id: str) -> dict:
        project = self._project(project_id)
        profile = self.artifact_service.resolve(project_id, profile_artifact_id)
        if profile["artifact_type"] != "data_profile":
            raise ValueError("Artifact must be a data profile")
        profile_path = self._validated_file(
            project, profile, {".json"}, "Data profile"
        )
        problem_specs = [
            item
            for item in self.store.list_artifacts(project_id)
            if item["artifact_type"] == "problem_spec"
        ]
        if not problem_specs:
            raise ValueError("Registered problem specification is required")
        problem_artifact = max(
            problem_specs, key=lambda item: (item["created_at"], item["artifact_id"])
        )
        problem_path = self._validated_file(
            project, problem_artifact, {".json"}, "Problem specification"
        )
        problem_spec = ProblemSpec.model_validate_json(
            problem_path.read_text(encoding="utf-8")
        ).model_dump(mode="json")
        profile_payload = json.loads(profile_path.read_text(encoding="utf-8"))
        if not isinstance(profile_payload, dict):
            raise ValueError("Data profile must be a JSON object")
        task, run = self.run_service.start(
            project_id,
            "model_planning",
            "modeling",
            "modeling_planner",
            {"profile_artifact_id": profile_artifact_id},
            ["analysis/model_plan.json", "analysis/model_plan.md"],
        )
        root = Path(project["workspace_path"])
        json_path = root / "analysis" / "model_plan.json"
        markdown_path = root / "analysis" / "model_plan.md"
        previous_outputs = {
            json_path: json_path.read_bytes() if json_path.exists() else None,
            markdown_path: markdown_path.read_bytes() if markdown_path.exists() else None,
        }
        registered_artifacts = []
        approval = None
        try:
            prompt = (
                "Return only JSON matching this schema. Propose at most three candidates and do not claim unrun results.\n"
                + json.dumps(ModelPlan.model_json_schema(), ensure_ascii=False)
                + "\nProblem specification:\n"
                + json.dumps(problem_spec, ensure_ascii=False)
                + "\nData profile:\n"
                + json.dumps(profile_payload, ensure_ascii=False)
            )
            model = ModelPlan.model_validate(parse_json_object(await self.llm.generate(prompt)))
            payload = model.model_dump(mode="json")
            self._atomic_write(
                json_path,
                (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode(
                    "utf-8"
                ),
            )
            self._atomic_write(
                markdown_path,
                self._model_plan_markdown(payload).encode("utf-8"),
            )
            plan_artifact = self.artifact_service.register(
                project_id,
                "model_plan",
                "analysis/model_plan.json",
                source_run_id=run["run_id"],
            )
            registered_artifacts.append(plan_artifact)
            markdown_artifact = self.artifact_service.register(
                project_id,
                "model_plan_report",
                "analysis/model_plan.md",
                source_run_id=run["run_id"],
            )
            registered_artifacts.append(markdown_artifact)
            approval_payload = {
                "artifact_id": plan_artifact["artifact_id"],
                "artifact_sha256": plan_artifact["sha256"],
                "version": plan_artifact["version"],
            }
            approval = self.approval_service.request(
                project_id, "model_approval", approval_payload
            )
            artifact_ids = [plan_artifact["artifact_id"], markdown_artifact["artifact_id"]]
            self.run_service.complete(task["task_id"], run["run_id"], artifact_ids)
            return {
                "model_plan": payload,
                "artifact": plan_artifact,
                "markdown_artifact": markdown_artifact,
                "approval": approval,
                "task_id": task["task_id"],
                "run_id": run["run_id"],
            }
        except Exception as error:
            if approval:
                self.approval_service.remove_request(project_id, approval["approval_id"])
            for artifact in reversed(registered_artifacts):
                self.artifact_service.remove(project_id, artifact["artifact_id"])
            for path, content in previous_outputs.items():
                self._restore(path, content)
            safe_error = self._safe_error(error)
            current = self.store.get_task(task["task_id"])
            if current and current["status"] == "running":
                self.run_service.fail(task, run["run_id"], safe_error)
            raise ValueError(safe_error) from error

    def _project(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        return project

    @staticmethod
    def _read_problem(path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _validated_file(
        project: dict, artifact: dict, suffixes: set[str], label: str
    ) -> Path:
        root = Path(project["workspace_path"]).resolve()
        target = (root / artifact["relative_path"]).resolve()
        if target == root or root not in target.parents:
            raise ValueError(f"{label} is outside project workspace")
        if target.suffix.lower() not in suffixes:
            raise ValueError(f"{label} has an unsupported file type")
        if not target.is_file():
            raise ValueError(f"{label} does not exist")
        if hashlib.sha256(target.read_bytes()).hexdigest() != artifact["sha256"]:
            raise ValueError(f"{label} hash does not match registered artifact")
        return target

    @staticmethod
    def _safe_error(error: Exception) -> str:
        if isinstance(error, json.JSONDecodeError):
            return "Agent output is not valid JSON"
        if isinstance(error, ValidationError):
            details = []
            for item in error.errors(include_input=False, include_url=False):
                location = ".".join(str(part) for part in item["loc"])
                details.append(f"{location}: {item['msg']}" if location else item["msg"])
            return ("Agent output validation failed: " + "; ".join(details))[:1000]
        return f"Modeling role failed ({type(error).__name__})"

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

    @classmethod
    def _restore(cls, path: Path, content: bytes | None) -> None:
        if content is None:
            path.unlink(missing_ok=True)
        else:
            cls._atomic_write(path, content)

    @staticmethod
    def _model_plan_markdown(payload: dict) -> str:
        lines = ["# Model Plan", "", payload["problem_summary"], ""]
        for index, candidate in enumerate(payload["candidates"], start=1):
            lines.extend(
                [
                    f"## {index}. {candidate['name']}",
                    "",
                    f"Algorithm: {candidate['algorithm']}",
                    f"Assumptions: {', '.join(candidate['assumptions']) or 'None'}",
                    f"Features: {', '.join(candidate['features']) or 'None'}",
                    f"Metrics: {', '.join(candidate['metrics']) or 'None'}",
                    f"Risks: {', '.join(candidate['risks']) or 'None'}",
                    "",
                ]
            )
        return "\n".join(lines)
