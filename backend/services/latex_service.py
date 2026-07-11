import hashlib
import json
import shutil
from pathlib import Path

from services.approval_service import canonical_hash
from services.restricted_runner import RestrictedRunner
from services.review_agent_service import ReviewAgentService


class LatexService:
    def __init__(self, store, artifact_service, approvals, placeholder_service=None, runner=None):
        self.store = store
        self.artifact_service = artifact_service
        self.approvals = approvals
        self.placeholder_service = placeholder_service
        self.runner = runner or RestrictedRunner()

    def current_payload(self, project_id: str) -> dict:
        project = self._project(project_id)
        artifacts = self.store.list_artifacts(project_id)
        sources = []
        for kind in ("paper_markdown", "paper_latex"):
            artifact = self._latest(artifacts, kind)
            path = self._path(project, artifact)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            sources.append({"artifact_id": artifact["artifact_id"], "artifact_type": kind, "sha256": digest, "version": artifact["version"]})
        review = self.store.latest_review(project_id)
        return {
            "sources": sources,
            "claims": self.store.list_paper_claims(project_id),
            "review_hash": review["paper_hash"] if review and review["status"] == "passed" else None,
        }

    def compile(self, project_id: str) -> dict:
        project = self._project(project_id)
        payload = self.current_payload(project_id)
        review = self.store.latest_review(project_id)
        current_review_hash = ReviewAgentService(self.store, None, None).current_paper_hash(project_id)
        if not review or review["status"] != "passed" or review["paper_hash"] != current_review_hash:
            raise ValueError("Paper review is not current")
        self.approvals.require_approved(project_id, "final_approval", canonical_hash(payload))
        root = Path(project["workspace_path"]).resolve()
        build = root / ".workflow" / "build" / "paper"
        if build.exists():
            shutil.rmtree(build)
        build.mkdir(parents=True)
        sources = {entry["artifact_type"]: entry for entry in payload["sources"]}
        markdown = self._path(project, self.store.get_artifact(sources["paper_markdown"]["artifact_id"]))
        latex = self._path(project, self.store.get_artifact(sources["paper_latex"]["artifact_id"]))
        build_markdown = build / "draft.md"
        build_main = build / "main.tex"
        build_markdown.write_text(self._resolve(project_id, markdown.read_text(encoding="utf-8")), encoding="utf-8")
        build_main.write_text(self._resolve(project_id, latex.read_text(encoding="utf-8")), encoding="utf-8")
        output = build / "output"
        output.mkdir()
        command = ["xelatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", str(output), str(build_main)]
        first = self.runner.run(command, build, 120, 2_000_000, False)
        second = self.runner.run(command, build, 120, 2_000_000, False)
        pdf = output / "main.pdf"
        if first.exit_code != 0 or second.exit_code != 0 or not pdf.is_file():
            raise ValueError("LaTeX compilation failed")
        deliverable = root / "deliverables" / "paper.pdf"
        deliverable.parent.mkdir(exist_ok=True)
        shutil.copy2(pdf, deliverable)
        return {"pdf_path": str(deliverable), "build_dir": str(build), "payload_hash": canonical_hash(payload)}

    def _resolve(self, project_id: str, content: str) -> str:
        if not self.placeholder_service:
            return content
        resolved, claims = self.placeholder_service.resolve_markdown(project_id, content)
        if claims:
            markdown = self._latest(self.store.list_artifacts(project_id), "paper_markdown")
            self.store.replace_paper_claims(project_id, markdown["artifact_id"], claims)
        return resolved

    def _project(self, project_id):
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        return project

    @staticmethod
    def _latest(artifacts, kind):
        candidates = [item for item in artifacts if item["artifact_type"] == kind]
        if not candidates:
            raise ValueError("Paper source is unavailable")
        return max(candidates, key=lambda item: (item["created_at"], item["artifact_id"]))

    @staticmethod
    def _path(project, artifact):
        root = Path(project["workspace_path"]).resolve()
        path = (root / artifact["relative_path"]).resolve()
        if path == root or root not in path.parents or not path.is_file():
            raise ValueError("Paper source is unavailable")
        return path
