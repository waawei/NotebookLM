import json
import re
import hashlib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError


class PaperDraftPayload(BaseModel):
    markdown: str = Field(min_length=100)
    latex: str = Field(min_length=100)


LITERAL_RESULT = re.compile(r"(?i)(rmse|mae|accuracy|precision|recall|f1|auc|r\^2|loss|score|error|mape)[^\n]{0,30}\b[0-9]+(?:\.\d+)?(?:e[+-]?\d+)?%?")


def require_placeholder_results(text: str) -> None:
    scrubbed = re.sub(r"\{\{metric:[^}]+\}\}", "", text)
    if LITERAL_RESULT.search(scrubbed):
        raise ValueError("Experimental results must use metric placeholders")


class PaperAgentService:
    def __init__(self, store, artifact_service, approval_service, run_service, llm):
        self.store = store
        self.artifact_service = artifact_service
        self.approval_service = approval_service
        self.run_service = run_service
        self.llm = llm

    async def create_draft(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        artifacts = self.store.list_artifacts(project_id)
        problem = self._current_artifact(project, artifacts, "problem_spec")
        plan = self._current_artifact(project, artifacts, "model_plan")
        plan_payload = {
            "artifact_id": plan["artifact_id"],
            "artifact_sha256": plan["sha256"],
            "version": plan["version"],
        }
        self.approval_service.require_approved(
            project_id, "model_approval", self._canonical_hash(plan_payload)
        )
        completed = [item for item in self.store.list_experiments(project_id) if item["status"] == "completed"]
        if not completed:
            raise ValueError("Paper draft requires a completed experiment")
        task, run = self.run_service.start(
            project_id, "paper_drafting", "writing", "modeling_paper_writer",
            {"problem_artifact_id": problem["artifact_id"], "model_plan_artifact_id": plan["artifact_id"]},
            ["paper/draft.md", "paper/main.tex"],
        )
        prompt = (
            "STAGE:paper_writer\nReturn only JSON containing markdown and latex. Use metric, figure, and table "
            "placeholders for every experimental fact; never type a measured value directly.\n"
            + json.dumps(PaperDraftPayload.model_json_schema(), ensure_ascii=False)
            + "\nAvailable artifacts:\n"
            + json.dumps(artifacts, ensure_ascii=False)
            + "\nPREDICTION_ARTIFACT_ID:"
            + next((item["artifact_id"] for item in artifacts if item["artifact_type"] == "experiment_figure"), "")
            + "\nProblem specification:\n" + self._read_artifact(project, problem)
            + "\nApproved model plan:\n" + self._read_artifact(project, plan)
        )
        try:
            payload = PaperDraftPayload.model_validate_json(await self.llm.generate(prompt))
        except (ValidationError, json.JSONDecodeError) as error:
            self.run_service.fail(task, run["run_id"], "Paper draft is not valid")
            raise ValueError("Paper draft is not valid") from error
        try:
            require_placeholder_results(payload.markdown)
            require_placeholder_results(payload.latex)
            root = Path(project["workspace_path"]).resolve()
            paper = root / "paper"
            paper.mkdir(exist_ok=True)
            (paper / "draft.md").write_text(payload.markdown, encoding="utf-8")
            (paper / "main.tex").write_text(payload.latex, encoding="utf-8")
            result = {
                "markdown_artifact": self.artifact_service.register(project_id, "paper_markdown", "paper/draft.md"),
                "latex_artifact": self.artifact_service.register(project_id, "paper_latex", "paper/main.tex"),
            }
            self.run_service.complete(task["task_id"], run["run_id"], [item["artifact_id"] for item in result.values()])
            return result
        except Exception as error:
            self.run_service.fail(task, run["run_id"], "Paper draft generation failed")
            raise error

    @staticmethod
    def _canonical_hash(payload: dict) -> str:
        from services.approval_service import canonical_hash
        return canonical_hash(payload)

    @staticmethod
    def _read_artifact(project: dict, artifact: dict) -> str:
        root = Path(project["workspace_path"]).resolve()
        path = (root / artifact["relative_path"]).resolve()
        if path == root or root not in path.parents or not path.is_file():
            raise ValueError("Paper source artifact is unavailable")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != artifact["sha256"]:
            raise ValueError("Paper source artifact has changed")
        return content.decode("utf-8")

    def _current_artifact(self, project: dict, artifacts: list[dict], kind: str) -> dict:
        candidates = [item for item in artifacts if item["artifact_type"] == kind]
        if not candidates:
            raise ValueError(f"Paper draft requires {kind}")
        artifact = max(candidates, key=lambda item: (item["created_at"], item["artifact_id"]))
        self._read_artifact(project, artifact)
        return artifact
