import json
import re
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError


class PaperDraftPayload(BaseModel):
    markdown: str = Field(min_length=100)
    latex: str = Field(min_length=100)


LITERAL_RESULT = re.compile(
    r"(?i)(rmse|mae|accuracy|precision|recall|f1|auc|r\^2)[^\n]{0,30}\b[0-9]+(?:\.[0-9]+)?"
)


def require_placeholder_results(text: str) -> None:
    scrubbed = re.sub(r"\{\{metric:[^}]+\}\}", "", text)
    if LITERAL_RESULT.search(scrubbed):
        raise ValueError("Experimental results must use metric placeholders")


class PaperAgentService:
    def __init__(self, store, artifact_service, llm):
        self.store = store
        self.artifact_service = artifact_service
        self.llm = llm

    async def create_draft(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        artifacts = self.store.list_artifacts(project_id)
        prompt = (
            "Return only JSON containing markdown and latex. Use metric, figure, and table "
            "placeholders for every experimental fact; never type a measured value directly.\n"
            + json.dumps(PaperDraftPayload.model_json_schema(), ensure_ascii=False)
            + "\nAvailable artifacts:\n"
            + json.dumps(artifacts, ensure_ascii=False)
        )
        try:
            payload = PaperDraftPayload.model_validate_json(await self.llm.generate(prompt))
        except (ValidationError, json.JSONDecodeError) as error:
            raise ValueError("Paper draft is not valid") from error
        require_placeholder_results(payload.markdown)
        require_placeholder_results(payload.latex)
        root = Path(project["workspace_path"]).resolve()
        paper = root / "paper"
        paper.mkdir(exist_ok=True)
        markdown_path = paper / "draft.md"
        latex_path = paper / "main.tex"
        markdown_path.write_text(payload.markdown, encoding="utf-8")
        latex_path.write_text(payload.latex, encoding="utf-8")
        return {
            "markdown_artifact": self.artifact_service.register(
                project_id, "paper_markdown", "paper/draft.md"
            ),
            "latex_artifact": self.artifact_service.register(
                project_id, "paper_latex", "paper/main.tex"
            ),
        }
