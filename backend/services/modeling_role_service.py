import json
from pathlib import Path

from PyPDF2 import PdfReader

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
        task, run = self.run_service.start(
            project_id,
            "problem_parsing",
            "modeling",
            "modeling_problem_parser",
            {"artifact_id": artifact_id},
            ["problem/problem_spec.json"],
        )
        try:
            problem_text = self._read_problem(
                Path(project["workspace_path"]) / artifact["relative_path"]
            )
            prompt = (
                "Return only JSON matching this schema. Do not invent requirements.\n"
                + json.dumps(ProblemSpec.model_json_schema(), ensure_ascii=False)
                + "\nCompetition prompt:\n"
                + problem_text
            )
            model = ProblemSpec.model_validate(parse_json_object(await self.llm.generate(prompt)))
            payload = model.model_dump(mode="json")
            output = Path(project["workspace_path"]) / "problem" / "problem_spec.json"
            output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
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
            self.run_service.fail(task, run["run_id"], str(error))
            raise ValueError(str(error)) from error

    async def create_model_plan(self, project_id: str, profile_artifact_id: str) -> dict:
        project = self._project(project_id)
        profile = self.artifact_service.resolve(project_id, profile_artifact_id)
        if profile["artifact_type"] != "data_profile":
            raise ValueError("Artifact must be a data profile")
        task, run = self.run_service.start(
            project_id,
            "model_planning",
            "modeling",
            "modeling_planner",
            {"profile_artifact_id": profile_artifact_id},
            ["analysis/model_plan.json", "analysis/model_plan.md"],
        )
        try:
            root = Path(project["workspace_path"])
            problem_spec = json.loads(
                (root / "problem" / "problem_spec.json").read_text(encoding="utf-8")
            )
            profile_payload = json.loads(
                (root / profile["relative_path"]).read_text(encoding="utf-8")
            )
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
            json_path = root / "analysis" / "model_plan.json"
            markdown_path = root / "analysis" / "model_plan.md"
            json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            markdown_path.write_text(self._model_plan_markdown(payload), encoding="utf-8")
            plan_artifact = self.artifact_service.register(
                project_id,
                "model_plan",
                "analysis/model_plan.json",
                source_run_id=run["run_id"],
            )
            markdown_artifact = self.artifact_service.register(
                project_id,
                "model_plan_report",
                "analysis/model_plan.md",
                source_run_id=run["run_id"],
            )
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
            self.run_service.fail(task, run["run_id"], str(error))
            raise ValueError(str(error)) from error

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
