"""Inspectable agent run APIs."""

from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()


class AgentRunCreate(BaseModel):
    skill_id: str
    doc_ids: List[str] = []
    request: str = ""


@router.get("/runs")
async def list_runs():
    runs = agent_service.list_runs()
    return {"runs": runs, "total": len(runs)}


@router.post("/runs")
async def create_run(request: AgentRunCreate, background_tasks: BackgroundTasks = None):
    try:
        run = agent_service.create_run(
            request.skill_id,
            {"doc_ids": request.doc_ids, "request": request.request},
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent run request")

    if background_tasks is not None:
        background_tasks.add_task(agent_service.execute_run, run["run_id"])
    return run


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = agent_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run
