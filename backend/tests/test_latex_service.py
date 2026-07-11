from pathlib import Path

import pytest

from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.latex_service import LatexService
from services.modeling_store import ModelingStore
from services.review_agent_service import ReviewAgentService


class FakeRunner:
    def __init__(self):
        self.commands = []

    def run(self, command, cwd, timeout, cap, network):
        self.commands.append(command)
        build = Path(command[command.index("-output-directory") + 1])
        build.mkdir(parents=True, exist_ok=True)
        (build / "main.pdf").write_bytes(b"%PDF-1.4\n")
        return type("Result", (), {"exit_code": 0})()


def pass_current_review(store, project):
    paper_hash = ReviewAgentService(store, None, None).current_paper_hash(project["project_id"])
    store.create_review_run(project["project_id"], paper_hash, [], "passed")


def test_latex_command_disables_shell_escape_and_requires_current_approval(tmp_path):
    workspace = tmp_path / "workspace"
    paper = workspace / "paper"
    paper.mkdir(parents=True)
    (paper / "draft.md").write_text("# Subproblem 1", encoding="utf-8")
    (paper / "main.tex").write_text("\\documentclass{article}\\begin{document}OK\\end{document}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    pass_current_review(store, project)
    service = LatexService(store, artifacts, ApprovalService(store), runner=FakeRunner())
    payload = service.current_payload(project["project_id"])
    request = service.approvals.request(project["project_id"], "final_approval", payload)
    service.approvals.decide(request["approval_id"], "approved", request["payload_hash"])

    result = service.compile(project["project_id"])

    assert "-no-shell-escape" in service.runner.commands[0]
    assert "-halt-on-error" in service.runner.commands[0]
    assert Path(result["pdf_path"]).is_file()


def test_compile_rejects_changed_source_after_approval(tmp_path):
    workspace = tmp_path / "workspace"
    paper = workspace / "paper"
    paper.mkdir(parents=True)
    (paper / "draft.md").write_text("# Subproblem 1", encoding="utf-8")
    source = paper / "main.tex"
    source.write_text("\\begin{document}OK\\end{document}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    pass_current_review(store, project)
    service = LatexService(store, artifacts, ApprovalService(store), runner=FakeRunner())
    request = service.approvals.request(project["project_id"], "final_approval", service.current_payload(project["project_id"]))
    service.approvals.decide(request["approval_id"], "approved", request["payload_hash"])
    source.write_text("changed", encoding="utf-8")

    with pytest.raises(ValueError, match="approval|review"):
        service.compile(project["project_id"])


def test_compile_rejects_approval_without_current_passing_review(tmp_path):
    workspace = tmp_path / "workspace"
    paper = workspace / "paper"
    paper.mkdir(parents=True)
    (paper / "draft.md").write_text("# Subproblem 1", encoding="utf-8")
    (paper / "main.tex").write_text("\\begin{document}OK\\end{document}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    service = LatexService(store, artifacts, ApprovalService(store), runner=FakeRunner())
    request = service.approvals.request(project["project_id"], "final_approval", service.current_payload(project["project_id"]))
    service.approvals.decide(request["approval_id"], "approved", request["payload_hash"])

    with pytest.raises(ValueError, match="review"):
        service.compile(project["project_id"])


def test_final_payload_includes_bibliography_hash(tmp_path):
    workspace = tmp_path / "workspace"
    paper = workspace / "paper"
    paper.mkdir(parents=True)
    (paper / "draft.md").write_text("# Subproblem 1", encoding="utf-8")
    (paper / "main.tex").write_text("\\begin{document}OK\\end{document}", encoding="utf-8")
    (paper / "references.bib").write_text("@article{source, title={Source}}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    bibliography = artifacts.register(project["project_id"], "paper_bibliography", "paper/references.bib")

    payload = LatexService(store, artifacts, ApprovalService(store), runner=FakeRunner()).current_payload(project["project_id"])

    assert payload["bibliography"]["artifact_id"] == bibliography["artifact_id"]


def test_final_payload_only_contains_claims_for_current_markdown(tmp_path):
    workspace = tmp_path / "workspace"
    paper = workspace / "paper"
    paper.mkdir(parents=True)
    (paper / "draft.md").write_text("# Current", encoding="utf-8")
    (paper / "main.tex").write_text("\\begin{document}OK\\end{document}", encoding="utf-8")
    store = ModelingStore(str(tmp_path / "modeling.db"))
    project = store.create_project("Forecast", "forecast", str(workspace), None)
    artifacts = ArtifactService(store)
    old = artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    (paper / "draft.md").write_text("# New", encoding="utf-8")
    current = artifacts.register(project["project_id"], "paper_markdown", "paper/draft.md")
    artifacts.register(project["project_id"], "paper_latex", "paper/main.tex")
    store.replace_paper_claims(project["project_id"], old["artifact_id"], [{
        "placeholder": "{{metric:old.validation_rmse}}", "claim_type": "metric", "artifact_id": "old-metric",
        "experiment_id": "exp-0001", "metric_name": "validation_rmse", "rendered_value": "9.99",
    }])

    payload = LatexService(store, artifacts, ApprovalService(store), runner=FakeRunner()).current_payload(project["project_id"])

    assert current["artifact_id"] == payload["sources"][0]["artifact_id"]
    assert payload["claims"] == []
