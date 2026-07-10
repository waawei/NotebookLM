"""Modeling project API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import PROJECT_ROOT, settings
from services.modeling_project_service import ModelingProjectService
from services.modeling_store import ModelingStore
from services.modeling_workspace import ModelingWorkspaceService


router = APIRouter()
project_service = ModelingProjectService(
    ModelingStore("./data/notebooklm.db"),
    ModelingWorkspaceService(settings.MODELING_WORKSPACE_ROOT, str(PROJECT_ROOT)),
)


class ProjectCreate(BaseModel):
    name: str
    deadline: str | None = None


class RollbackRequest(BaseModel):
    reason: str


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
    tasks = project_service.list_tasks(project_id)
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/projects/{project_id}/runs")
async def list_project_runs(project_id: str):
    runs = project_service.list_runs(project_id)
    return {"runs": runs, "total": len(runs)}
