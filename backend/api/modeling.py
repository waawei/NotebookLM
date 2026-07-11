"""Modeling project API endpoints."""

import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
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
    _require_state(project_id, "project_initialized")
    clean_kind = await validate_input_kind(InputUploadKind(kind=kind))
    if not file.filename:
        raise HTTPException(status_code=400, detail="Input filename is required")
    try:
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
        raise HTTPException(status_code=409, detail=str(error)) from error
