import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

from fakes.fake_modeling_llm import FakeModelingLLM
from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.data_profile_service import DataProfileService
from services.delivery_service import DeliveryService
from services.document_metadata_store import DocumentMetadataStore
from services.experiment_contracts import ExperimentConfig
from services.experiment_service import ExperimentService
from services.execution_policy import ExecutionPolicy
from services.git_commit_service import GitCommitService
from services.git_policy_service import GitPolicyService
from services.latex_service import LatexService
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_code_agent_service import ModelingCodeAgentService
from services.modeling_gate_service import ModelingGateService
from services.modeling_input_service import ModelingInputService
from services.modeling_project_service import ModelingProjectService
from services.modeling_recovery_service import ModelingRecoveryService
from services.modeling_role_service import ModelingRoleService
from services.modeling_store import ModelingStore
from services.modeling_workspace import ModelingWorkspaceService
from services.paper_agent_service import PaperAgentService
from services.paper_claim_service import PaperClaimService
from services.paper_placeholder_service import PaperPlaceholderService
from services.review_agent_service import ReviewAgentService


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "modeling_competition"


@pytest.fixture
def modeling_harness(tmp_path):
    return ModelingHarness(tmp_path)


def test_modeling_workflow_produces_traceable_pdf_and_commit(modeling_harness):
    project = modeling_harness.create_project("Fixture Forecast")
    modeling_harness.import_fixture(project)
    modeling_harness.parse_profile_and_plan(project)
    modeling_harness.approve_current(project, "model_approval")
    modeling_harness.prepare_approve_and_run(project, candidate_index=0)
    modeling_harness.prepare_approve_and_run(project, candidate_index=1)
    modeling_harness.validate_results(project)
    modeling_harness.write_and_review_paper(project)
    modeling_harness.approve_current(project, "final_approval")
    modeling_harness.compile_paper(project)
    modeling_harness.build_deliverables(project)
    approved_commit = modeling_harness.review_and_approve_commit(
        project, "feat: add fixture modeling solution"
    )
    assert approved_commit["state"] == "commit_approval_pending"
    result = modeling_harness.commit(project)

    assert result["state"] == "completed"
    assert modeling_harness.unresolved_claims(project) == []
    assert modeling_harness.git_log(project, 1)[0]["subject"] == (
        "feat: add fixture modeling solution"
    )
    assert (Path(project["workspace_path"]) / "deliverables" / "paper.pdf").is_file()


def test_restart_recovery_terminates_running_experiment_and_allocates_new_id(
    modeling_harness,
):
    project = modeling_harness.create_project("Interrupted Fixture")
    modeling_harness.import_fixture(project)
    modeling_harness.parse_profile_and_plan(project)
    modeling_harness.approve_current(project, "model_approval")
    prepared = modeling_harness.prepare_experiment(project, candidate_index=0)
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        cwd=project["workspace_path"],
    )
    modeling_harness.store.update_state(project["project_id"], "experiment_running")
    modeling_harness.store.update_experiment_status(
        prepared["experiment"]["experiment_id"], "running", pid=process.pid
    )

    recovered = ModelingRecoveryService(
        ModelingStore(modeling_harness.store.db_path), modeling_harness.agent_store
    ).recover_interrupted_projects()

    process.wait(timeout=10)
    interrupted = modeling_harness.store.get_experiment(
        prepared["experiment"]["experiment_id"]
    )
    next_experiment = modeling_harness.prepare_experiment(project, candidate_index=1)

    assert recovered == [{
        "project_id": project["project_id"],
        "recovered_from": "experiment_running",
        "recovered_to": "experiment_implementation",
    }]
    assert process.returncode is not None
    assert interrupted["status"] == "failed"
    assert interrupted["error_code"] == "interrupted"
    assert modeling_harness.store.get_project(project["project_id"])["state"] == (
        "experiment_implementation"
    )
    assert next_experiment["experiment"]["experiment_id"] != interrupted["experiment_id"]


class ModelingHarness:
    def __init__(self, tmp_path: Path):
        self.store = ModelingStore(str(tmp_path / "modeling.db"))
        self.agent_store = DocumentMetadataStore(str(tmp_path / "agents.db"))
        self.artifacts = ArtifactService(self.store)
        self.approvals = ApprovalService(self.store)
        self.workspace = ModelingWorkspaceService(
            str(tmp_path / "workspaces"), str(tmp_path / "application")
        )
        self.projects = ModelingProjectService(
            self.store,
            self.workspace,
            self.agent_store,
            ModelingGateService(self.store, self.approvals),
        )
        self.inputs = ModelingInputService(self.store, self.artifacts, 1_000_000)
        self.profile = DataProfileService(self.store, self.artifacts)
        self.runs = ModelingAgentRunService(self.store, self.agent_store)
        self.llm = FakeModelingLLM()
        self.roles = ModelingRoleService(
            self.store, self.artifacts, self.approvals, self.runs, self.llm
        )
        self.code = ModelingCodeAgentService(
            self.store, self.artifacts, self.approvals, self.runs, self.llm
        )
        self.execution_policy = ExecutionPolicy(self.approvals)
        self.experiments = ExperimentService(
            self.store, self.artifacts, self.execution_policy
        )
        self.placeholders = PaperPlaceholderService(self.store, self.artifacts)
        self.paper = PaperAgentService(
            self.store, self.artifacts, self.approvals, self.runs, self.llm
        )
        self.reviewer = ReviewAgentService(self.store, self.artifacts, self.llm)
        self.latex = LatexService(
            self.store, self.artifacts, self.approvals, self.placeholders
        )
        self.delivery = DeliveryService(self.store, self.artifacts)
        self.git = GitCommitService(
            self.store,
            self.approvals,
            GitPolicyService(),
            self.delivery.reproducibility,
        )

    def create_project(self, name: str) -> dict:
        project = self.projects.create_project(name)
        for command in (
            ["git", "config", "user.email", "fixture@example.test"],
            ["git", "config", "user.name", "Fixture Workflow"],
        ):
            subprocess.run(command, cwd=project["workspace_path"], check=True)
        return project

    def import_fixture(self, project: dict) -> None:
        problem = self.inputs.import_input(
            project["project_id"],
            "problem.txt",
            (FIXTURE_ROOT / "problem.txt").read_bytes(),
            "problem",
        )
        data = self.inputs.import_input(
            project["project_id"],
            "train.csv",
            (FIXTURE_ROOT / "train.csv").read_bytes(),
            "data",
        )
        project["problem_artifact_id"] = problem["artifact_id"]
        project["data_artifact_id"] = data["artifact_id"]

    def parse_profile_and_plan(self, project: dict) -> None:
        self.projects.advance(project["project_id"])
        asyncio.run(self.roles.parse_problem(project["project_id"], project["problem_artifact_id"]))
        self.projects.advance(project["project_id"])
        self.profile.profile(project["project_id"], project["data_artifact_id"])
        self.projects.advance(project["project_id"])
        profile = self._latest_artifact(project, "data_profile")
        asyncio.run(self.roles.create_model_plan(project["project_id"], profile["artifact_id"]))
        self.projects.advance(project["project_id"])

    def approve_current(self, project: dict, gate: str) -> None:
        request = next(
            request
            for request in reversed(self.approvals.list_for_project(project["project_id"]))
            if request["gate"] == gate and request["status"] == "pending"
        )
        self.approvals.decide(request["approval_id"], "approved", request["payload_hash"])
        if gate in {"model_approval", "final_approval"}:
            self.projects.advance(project["project_id"])

    def prepare_experiment(self, project: dict, candidate_index: int) -> dict:
        return asyncio.run(self.code.prepare_experiment(project["project_id"], candidate_index))

    def prepare_approve_and_run(self, project: dict, candidate_index: int) -> dict:
        prepared = self.prepare_experiment(project, candidate_index)
        batch = ExperimentConfig.model_validate(prepared["experiment"]["config"])
        assert batch.experiment_id == prepared["experiment"]["experiment_id"]
        from services.experiment_contracts import ExecutionBatch

        execution = ExecutionBatch.model_validate(prepared["batch"])
        request = self.execution_policy.request_execution(project, execution)
        self.approvals.decide(request["approval_id"], "approved", request["payload_hash"])
        self.store.set_experiment_execution_batch(
            prepared["experiment"]["experiment_id"],
            request["payload_hash"],
            execution.model_dump(mode="json"),
        )
        return self.experiments.execute(
            project["project_id"], prepared["experiment"]["experiment_id"]
        )

    def validate_results(self, project: dict) -> None:
        self.projects.advance(project["project_id"])
        self.projects.advance(project["project_id"])
        self.projects.advance(project["project_id"])

    def write_and_review_paper(self, project: dict) -> None:
        drafted = asyncio.run(self.paper.create_draft(project["project_id"]))
        markdown = (Path(project["workspace_path"]) / "paper" / "draft.md").read_text(
            encoding="utf-8"
        )
        _, claims = self.placeholders.resolve_markdown(project["project_id"], markdown)
        PaperClaimService(self.store).replace_for_paper(
            project["project_id"], drafted["markdown_artifact"]["artifact_id"], claims
        )
        self.projects.advance(project["project_id"])
        review = asyncio.run(self.reviewer.review(project["project_id"]))
        assert review["status"] == "passed"
        self.projects.advance(project["project_id"])
        self.approvals.request(
            project["project_id"],
            "final_approval",
            self.latex.current_payload(project["project_id"]),
        )

    def compile_paper(self, project: dict) -> dict:
        return self.latex.compile(project["project_id"])

    def build_deliverables(self, project: dict) -> dict:
        built = self.delivery.build(project["project_id"])
        self.projects.advance(project["project_id"])
        return built

    def review_and_approve_commit(self, project: dict, message: str) -> dict:
        root = Path(project["workspace_path"])
        paths = [
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and ".venv" not in path.parts
            and ".workflow" not in path.parts
            and ".pytest_cache" not in path.parts
            and "__pycache__" not in path.parts
            and path.relative_to(root).as_posix() != "data/raw/train.csv"
        ]
        request = self.git.request_commit(project["project_id"], paths, message)
        self.approvals.decide(request["approval_id"], "approved", request["payload_hash"])
        state = self.projects.advance(project["project_id"])
        return {"paths": paths, "request": request, "state": state["state"]}

    def commit(self, project: dict) -> dict:
        request = self.review_and_approve_commit
        del request
        records = self.store.list_approval_requests(project["project_id"])
        approval = next(
            item for item in reversed(records) if item["gate"] == "commit_approval"
        )
        payload = approval["payload"]
        self.git.commit(project["project_id"], payload["paths"], payload["commit_message"])
        committing = self.projects.advance(project["project_id"])
        assert committing["state"] == "committing"
        return self.projects.advance(project["project_id"])

    def unresolved_claims(self, project: dict) -> list[dict]:
        review = self.store.latest_review(project["project_id"])
        return [
            issue for issue in review["issues"] if issue["code"] == "unresolved_placeholder"
        ]

    def git_log(self, project: dict, count: int) -> list[dict]:
        result = subprocess.run(
            ["git", "log", f"-{count}", "--pretty=%s"],
            cwd=project["workspace_path"],
            check=True,
            capture_output=True,
            text=True,
        )
        return [{"subject": subject} for subject in result.stdout.splitlines()]

    def _latest_artifact(self, project: dict, artifact_type: str) -> dict:
        artifacts = [
            artifact
            for artifact in self.store.list_artifacts(project["project_id"])
            if artifact["artifact_type"] == artifact_type
        ]
        return max(artifacts, key=lambda artifact: (artifact["created_at"], artifact["artifact_id"]))
