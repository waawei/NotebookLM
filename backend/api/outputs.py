"""
Generated outputs API routes.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.output_service import OutputService

router = APIRouter()
output_service = OutputService()


class OutputGenerateRequest(BaseModel):
    kind: str
    source_doc_ids: list[str]


@router.get("")
async def list_outputs(kind: Optional[str] = None, include_archived: bool = False):
    try:
        outputs = output_service.list_outputs(kind, include_archived=include_archived)
        return {"outputs": outputs, "total": len(outputs)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate")
async def generate_output(request: OutputGenerateRequest):
    try:
        return await output_service.generate_output(
            kind=request.kind,
            source_doc_ids=request.source_doc_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{output_id}/export")
async def export_output(output_id: str):
    try:
        export = output_service.export_output(output_id)
        if not export:
            raise HTTPException(status_code=404, detail="Output not found")
        return export
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{output_id}/archive")
async def archive_output(output_id: str):
    archived = output_service.archive_output(output_id)
    if not archived:
        raise HTTPException(status_code=404, detail="Output not found")
    return {"message": "Output archived successfully"}


@router.post("/{output_id}/restore")
async def restore_output(output_id: str):
    restored = output_service.restore_output(output_id)
    if not restored:
        raise HTTPException(status_code=404, detail="Output not found")
    return {"message": "Output restored successfully"}


@router.get("/{output_id}")
async def get_output(output_id: str):
    output = output_service.get_output(output_id)
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    return output


@router.delete("/{output_id}")
async def delete_output(output_id: str):
    deleted = output_service.delete_output(output_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Output not found")
    return {"message": "Output deleted successfully"}
