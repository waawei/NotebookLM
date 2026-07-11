"""Modeling project API endpoints."""

import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.config import PROJECT_ROOT, settings
from services.approval_service import ApprovalService
from services.artifact_service import ArtifactService
from services.data_profile_service import DataProfileService
from services.llm_service import LLMService
from services.modeling_agent_run_service import ModelingAgentRunService
from services.modeling_gate_service import ModelingGateService
from services.modeling_input_service import ModelingInputService
from services.modeling_project_service import ModelingProjectService
from services.modeling_role_service import ModelingRoleService
from services.modeling_store import ModelingStore
from services.modeling_workspace import ModelingWorkspaceService
from services.modeling_code_agent_service import ModelingCodeAgentService
from services.execution_policy import ExecutionPolicy
from services.experiment_service import ExperimentService
from services.experiment_contracts import ExecutionBatch
from services.paper_agent_service import PaperAgentService
from services.paper_claim_service import PaperClaimService
from services.paper_placeholder_service import PaperPlaceholderService
from services.review_agent_service import ReviewAgentService
from services.latex_service import LatexService


router = APIRouter()
data_dir = Path(settings.UPLOAD_DIR).resolve().parent
data_dir.mkdir(parents=True, exist_ok=True)
modeling_store = ModelingStore(str(data_dir / "notebooklm.db"))
approval_service = ApprovalService(modeling_store)
artifact_service = ArtifactService(modeling_store)
project_service = ModelingProjectService(
    modeling_store,
    ModelingWorkspaceService(settings.MODELING_WORKSPACE_ROOT, str(PROJECT_ROOT)),
    gate_service=ModelingGateService(modeling_store, approval_service),
)
input_service = ModelingInputService(
    modeling_store, artifact_service, settings.MAX_FILE_SIZE
)
profile_service = DataProfileService(modeling_store, artifact_service)
run_service = ModelingAgentRunService(modeling_store, project_service.agent_store)
role_service = ModelingRoleService(
    modeling_store,
    artifact_service,
    approval_service,
    run_service,
    LLMService(),
)
code_agent_service = ModelingCodeAgentService(
    modeling_store, artifact_service, approval_service, run_service, LLMService()
)
execution_policy = ExecutionPolicy(approval_service)
experiment_service = ExperimentService(modeling_store, artifact_service, execution_policy)
paper_placeholder_service = PaperPlaceholderService(modeling_store, artifact_service)
paper_agent_service = PaperAgentService(modeling_store, artifact_service, approval_service, run_service, LLMService())
review_agent_service = ReviewAgentService(modeling_store, artifact_service, LLMService())
latex_service = LatexService(modeling_store, artifact_service, approval_service, paper_placeholder_service)


class ProjectCreate(BaseModel):
    name: str
    deadline: str | None = None


class RollbackRequest(BaseModel):
    reason: str


class InputUploadKind(BaseModel):
    kind: str


class ApprovalDecision(BaseModel):
    decision: str
    payload_hash: str
    comment: str = ""


class PaperSaveRequest(BaseModel):
    markdown: str


async def validate_input_kind(request: InputUploadKind) -> str:
    if request.kind not in {"problem", "data"}:
        raise HTTPException(status_code=400, detail="Input kind must be problem or data")
    return request.kind


def _require_project(project_id: str) -> dict:
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Modeling project not found")
    return project


def _require_state(project_id: str, expected: str) -> dict:
    project = _require_project(project_id)
    if project["state"] != expected:
        raise HTTPException(
            status_code=409,
            detail=f"Action requires workflow state: {expected}",
        )
    return project


def _latest_artifact(project_id: str, artifact_type: str) -> dict:
    artifacts = [
        item
        for item in artifact_service.list_for_project(project_id)
        if item["artifact_type"] == artifact_type
    ]
    if not artifacts:
        raise HTTPException(
            status_code=404, detail=f"{artifact_type} artifact not found"
        )
    return max(artifacts, key=lambda item: (item["created_at"], item["artifact_id"]))


@router.post("/projects")
async def create_project(request: ProjectCreate):
    try:
        return project_service.create_project(request.name, request.deadline)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects")
async def list_projects():
    projects = project_service.list_projects()
    return {"projects": projects, "total": len(projects)}


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Modeling project not found")
    return project


@router.post("/projects/{project_id}/advance")
async def advance_project(project_id: str):
    try:
        return project_service.advance(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/projects/{project_id}/rollback")
async def rollback_project(project_id: str, request: RollbackRequest):
    try:
        return project_service.rollback(project_id, request.reason)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/projects/{project_id}/tasks")
async def list_project_tasks(project_id: str):
    try:
        tasks = project_service.list_tasks(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/projects/{project_id}/runs")
async def list_project_runs(project_id: str):
    try:
        runs = project_service.list_runs(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"runs": runs, "total": len(runs)}


@router.post("/projects/{project_id}/inputs")
async def upload_input(
    project_id: str,
    file: UploadFile = File(...),
    kind: str = "problem",
):
    try:
        _require_state(project_id, "project_initialized")
        clean_kind = await validate_input_kind(InputUploadKind(kind=kind))
        if not file.filename:
            raise HTTPException(status_code=400, detail="Input filename is required")
        content = await file.read(settings.MAX_FILE_SIZE + 1)
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Input file exceeds size limit")
        return input_service.import_input(
            project_id, file.filename, content, clean_kind
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        await file.close()


@router.post("/projects/{project_id}/problem/parse")
async def parse_problem(project_id: str):
    _require_state(project_id, "problem_parsing")
    problem = _latest_artifact(project_id, "problem_input")
    try:
        return await role_service.parse_problem(project_id, problem["artifact_id"])
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/projects/{project_id}/data/profile/{artifact_id}")
async def profile_data(project_id: str, artifact_id: str):
    _require_state(project_id, "data_profiling")
    try:
        return profile_service.profile(project_id, artifact_id)
    except ValueError as error:
        status = 404 if "not found" in str(error).lower() else 400
        raise HTTPException(status_code=status, detail=str(error)) from error


@router.post("/projects/{project_id}/model-plan")
async def create_model_plan(project_id: str):
    _require_state(project_id, "model_planning")
    profile = _latest_artifact(project_id, "data_profile")
    try:
        return await role_service.create_model_plan(
            project_id, profile["artifact_id"]
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/projects/{project_id}/artifacts")
async def list_artifacts(project_id: str):
    _require_project(project_id)
    artifacts = artifact_service.list_for_project(project_id)
    return {"artifacts": artifacts, "total": len(artifacts)}


@router.get("/projects/{project_id}/artifacts/{artifact_id}")
async def get_artifact(project_id: str, artifact_id: str):
    project = _require_project(project_id)
    try:
        artifact = artifact_service.resolve(project_id, artifact_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    root = Path(project["workspace_path"]).resolve()
    target = (root / artifact["relative_path"]).resolve()
    if target == root or root not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found")
    try:
        content = json.loads(target.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        content = target.read_text(encoding="utf-8", errors="replace")
    return {**artifact, "content": content}


@router.get("/projects/{project_id}/approvals")
async def list_approvals(project_id: str):
    _require_project(project_id)
    approvals = approval_service.list_for_project(project_id)
    return {"approvals": approvals, "total": len(approvals)}


@router.post("/projects/{project_id}/approvals/{approval_id}/decide")
async def decide_approval(
    project_id: str, approval_id: str, request: ApprovalDecision
):
    _require_project(project_id)
    if request.decision not in {"approved", "changes_requested", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid approval decision")
    if request.decision == "changes_requested" and not request.comment.strip():
        raise HTTPException(
            status_code=400, detail="A comment is required when requesting changes"
        )
    try:
        return approval_service.decide_for_project(
            project_id,
            approval_id,
            request.decision,
            request.payload_hash,
            request.comment.strip(),
        )
    except ValueError as error:
        detail = str(error)
        if "not found" in detail.lower():
            status = 404
        elif "invalid approval decision" in detail.lower():
            status = 400
        else:
            status = 409
        raise HTTPException(status_code=status, detail=detail) from error


@router.post("/projects/{project_id}/experiments/prepare")
async def prepare_experiment(project_id: str, candidate_index: int = 0):
    _require_state(project_id, "experiment_implementation")
    try:
        return await code_agent_service.prepare_experiment(project_id, candidate_index)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/projects/{project_id}/experiments")
async def list_experiments(project_id: str):
    _require_project(project_id)
    experiments = modeling_store.list_experiments(project_id)
    artifacts = artifact_service.list_for_project(project_id)
    for experiment in experiments:
        experiment["artifacts"] = [
            item
            for item in artifacts
            if item.get("source_experiment_id") == experiment["experiment_id"]
        ]
    return {"experiments": experiments, "total": len(experiments)}


@router.get("/projects/{project_id}/experiments/{experiment_id}")
async def get_experiment(project_id: str, experiment_id: str):
    _require_project(project_id)
    experiment = modeling_store.get_experiment(experiment_id)
    if not experiment or experiment["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    experiment["artifacts"] = [
        item
        for item in artifact_service.list_for_project(project_id)
        if item.get("source_experiment_id") == experiment_id
    ]
    return experiment


@router.post("/projects/{project_id}/experiments/{experiment_id}/request-execution")
async def request_experiment_execution(project_id: str, experiment_id: str):
    project = _require_state(project_id, "execution_approval_pending")
    experiment = modeling_store.get_experiment(experiment_id)
    if not experiment or experiment["project_id"] != project_id or "execution_batch" not in experiment:
        raise HTTPException(status_code=404, detail="Prepared experiment not found")
    try:
        batch = ExecutionBatch.model_validate(experiment["execution_batch"])
        request = execution_policy.request_execution(project, batch)
        modeling_store.set_experiment_execution_batch(experiment_id, request["payload_hash"], batch.model_dump(mode="json"))
        return request
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/projects/{project_id}/experiments/{experiment_id}/execute")
async def execute_experiment(project_id: str, experiment_id: str):
    _require_state(project_id, "execution_approval_pending")
    try:
        return experiment_service.execute(project_id, experiment_id)
    except ValueError as error:
        detail = str(error)
        status = 409 if "approval" in detail.lower() or "content" in detail.lower() else 400
        raise HTTPException(status_code=status, detail=detail) from error


@router.post("/projects/{project_id}/paper/draft")
async def create_paper_draft(project_id: str):
    _require_project(project_id)
    try:
        return await paper_agent_service.create_draft(project_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.put("/projects/{project_id}/paper/markdown")
async def save_paper_markdown(project_id: str, request: PaperSaveRequest):
    project = _require_project(project_id)
    root = Path(project["workspace_path"]).resolve()
    path = (root / "paper" / "draft.md").resolve()
    if root not in path.parents:
        raise HTTPException(status_code=400, detail="Paper path is invalid")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(request.markdown, encoding="utf-8")
    try:
        return artifact_service.register(project_id, "paper_markdown", "paper/draft.md")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/projects/{project_id}/paper/render")
async def render_paper(project_id: str):
    _require_project(project_id)
    markdown = _latest_artifact(project_id, "paper_markdown")
    try:
        content = _paper_content(project_id, markdown)
        rendered, claims = paper_placeholder_service.resolve_markdown(project_id, content)
        PaperClaimService(modeling_store).replace_for_paper(project_id, markdown["artifact_id"], claims)
        return {"rendered": rendered, "claims": modeling_store.list_paper_claims(project_id, markdown["artifact_id"])}
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/projects/{project_id}/paper/review")
async def review_paper(project_id: str):
    _require_project(project_id)
    try:
        return await review_agent_service.review(project_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/projects/{project_id}/paper/reviews")
async def list_paper_reviews(project_id: str):
    _require_project(project_id)
    review = modeling_store.latest_review(project_id)
    return {"reviews": [review] if review else [], "total": 1 if review else 0}


@router.post("/projects/{project_id}/paper/request-final-approval")
async def request_final_paper_approval(project_id: str):
    _require_project(project_id)
    try:
        ModelingGateService(modeling_store, approval_service)._require_current_review(project_id)
        return approval_service.request(project_id, "final_approval", latex_service.current_payload(project_id))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/projects/{project_id}/paper/compile")
async def compile_paper(project_id: str):
    _require_project(project_id)
    try:
        return latex_service.compile(project_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/projects/{project_id}/paper/pdf")
async def get_paper_pdf(project_id: str):
    project = _require_project(project_id)
    root = Path(project["workspace_path"]).resolve()
    path = (root / "deliverables" / "paper.pdf").resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Paper PDF not found")
    return FileResponse(path, media_type="application/pdf", filename="paper.pdf")


def _paper_content(project_id: str, artifact: dict) -> str:
    project = _require_project(project_id)
    root = Path(project["workspace_path"]).resolve()
    path = (root / artifact["relative_path"]).resolve()
    if path == root or root not in path.parents or not path.is_file():
        raise ValueError("Paper source is unavailable")
    return path.read_text(encoding="utf-8")
