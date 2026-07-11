import hashlib
from pathlib import Path

from services.delivery_contracts import ReproductionCheck, ReproductionIssue


class ReproducibilityService:
    REQUIRED_FILES = {
        "deliverables/paper.pdf": "missing_pdf",
        "paper/draft.md": "missing_paper_markdown",
        "paper/main.tex": "missing_paper_latex",
        "requirements.txt": "missing_dependencies",
        "reproduce.ps1": "missing_reproduce_command",
    }
    EXPERIMENT_FILES = ("config.json", "metrics.json", "environment.json", "run.log")

    def __init__(self, store):
        self.store = store

    def check(self, project_id: str) -> dict:
        issues = self._collect_issues(project_id)
        return ReproductionCheck(
            ok=not any(item.blocking for item in issues), issues=issues
        ).model_dump(mode="json")

    def _collect_issues(self, project_id: str) -> list[ReproductionIssue]:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        root = Path(project["workspace_path"]).resolve()
        issues = []
        for relative_path, code in self.REQUIRED_FILES.items():
            if not (root / relative_path).is_file():
                issues.append(self._issue(code, relative_path))
        source = root / "src"
        if not source.is_dir() or not any(path.is_file() for path in source.rglob("*")):
            issues.append(self._issue("missing_source_code", "src"))
        completed = [
            experiment for experiment in self.store.list_experiments(project_id)
            if experiment["status"] == "completed"
        ]
        if len(completed) < 2:
            issues.append(self._issue("missing_completed_experiments", "completed experiments"))
        for experiment in completed:
            directory = root / "experiments" / experiment["experiment_id"]
            for filename in self.EXPERIMENT_FILES:
                if not (directory / filename).is_file():
                    issues.append(self._issue("missing_experiment_evidence", f"{experiment['experiment_id']}/{filename}"))
        artifacts = self.store.list_artifacts(project_id)
        artifact_by_id = {artifact["artifact_id"]: artifact for artifact in artifacts}
        for artifact in artifacts:
            if not self._matches_hash(root, artifact):
                issues.append(self._issue("artifact_hash_mismatch", artifact["relative_path"]))
        for claim in self.store.list_paper_claims(project_id):
            target = artifact_by_id.get(claim["artifact_id"])
            if target is None or not self._matches_hash(root, target):
                issues.append(self._issue("missing_paper_claim_target", claim["placeholder"]))
        return issues

    @staticmethod
    def _matches_hash(root: Path, artifact: dict) -> bool:
        target = (root / artifact["relative_path"]).resolve()
        if target == root or root not in target.parents or not target.is_file():
            return False
        return hashlib.sha256(target.read_bytes()).hexdigest() == artifact["sha256"]

    @staticmethod
    def _issue(code: str, subject: str) -> ReproductionIssue:
        return ReproductionIssue(code=code, message=f"Required delivery input is unavailable: {subject}", blocking=True)
