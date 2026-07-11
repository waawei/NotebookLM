import hashlib
import json
import re
from pathlib import Path

from pydantic import ValidationError

from services.paper_contracts import ReviewIssue


class ReviewAgentService:
    def __init__(self, store, artifact_service, llm):
        self.store = store
        self.artifact_service = artifact_service
        self.llm = llm

    async def review(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        artifacts = self.store.list_artifacts(project_id)
        markdown = self._latest(artifacts, "paper_markdown")
        latex = self._latest(artifacts, "paper_latex")
        issues = self._deterministic(project, markdown, latex)
        prompt = "Return only JSON with issues.\n" + json.dumps({"markdown": self._content(project, markdown), "latex": self._content(project, latex)})
        try:
            raw = json.loads(await self.llm.generate(prompt))
            issues.extend(ReviewIssue.model_validate(item).model_dump() for item in raw.get("issues", []))
        except (json.JSONDecodeError, ValidationError, TypeError) as error:
            raise ValueError("Paper review is not valid") from error
        paper_hash = self._paper_hash(markdown, latex)
        status = "failed" if any(item["severity"] == "blocking" for item in issues) else "passed"
        return self.store.create_review_run(project_id, paper_hash, issues, status)

    def _deterministic(self, project, markdown, latex):
        issues = []
        markdown_text = self._content(project, markdown)
        latex_text = self._content(project, latex)
        if re.search(r"\{\{(?:metric|figure|table):[^}]+\}\}", markdown_text + latex_text):
            issues.append(self._issue("unresolved_placeholder", "Paper contains unresolved placeholders", "Paper"))
        if not re.search(r"(?im)^#+\s*subproblem", markdown_text):
            issues.append(self._issue("missing_subproblem_headings", "Paper is missing subproblem headings", "Markdown"))
        if "\\begin{document}" not in latex_text or "\\end{document}" not in latex_text:
            issues.append(self._issue("invalid_latex_document", "LaTeX document boundaries are missing", "LaTeX"))
        return issues

    @staticmethod
    def _issue(code, message, location):
        return ReviewIssue(severity="blocking", code=code, message=message, location=location, artifact_ids=[]).model_dump()

    @staticmethod
    def _latest(artifacts, kind):
        matches = [item for item in artifacts if item["artifact_type"] == kind]
        if not matches:
            raise ValueError("Paper artifact is unavailable")
        return max(matches, key=lambda item: (item["created_at"], item["artifact_id"]))

    @staticmethod
    def _content(project, artifact):
        root = Path(project["workspace_path"]).resolve()
        path = (root / artifact["relative_path"]).resolve()
        if path == root or root not in path.parents or not path.is_file():
            raise ValueError("Paper artifact is unavailable")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
            raise ValueError("Paper artifact hash mismatch")
        return data.decode("utf-8")

    @staticmethod
    def _paper_hash(markdown, latex):
        return hashlib.sha256(f"{markdown['sha256']}:{latex['sha256']}".encode("ascii")).hexdigest()
