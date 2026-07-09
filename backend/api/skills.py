"""Read-only APIs for local agent skill manifests."""

from fastapi import APIRouter, HTTPException

from services.skill_service import SkillService

router = APIRouter()
skill_service = SkillService()


@router.get("")
async def list_skills():
    return {"skills": skill_service.list_skills()}


@router.get("/{skill_id}")
async def get_skill(skill_id: str):
    skill = skill_service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill
