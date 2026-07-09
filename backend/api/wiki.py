"""
Wiki page API routes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.wiki_service import WikiService

router = APIRouter()
wiki_service = WikiService()


class WikiPageCreate(BaseModel):
    title: str
    content: str
    source_doc_ids: list[str] = []


class WikiPageUpdate(BaseModel):
    title: str
    content: str


class WikiPageGenerate(BaseModel):
    title: str
    source_doc_ids: list[str]


@router.get("/pages")
async def list_pages():
    try:
        pages = wiki_service.list_pages()
        return {"pages": pages, "total": len(pages)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pages")
async def create_page(request: WikiPageCreate):
    try:
        return wiki_service.create_page(
            title=request.title,
            content=request.content,
            source_doc_ids=request.source_doc_ids,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/pages/{page_id}")
async def get_page(page_id: str):
    page = wiki_service.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Wiki page not found")
    return page


@router.put("/pages/{page_id}")
async def update_page(page_id: str, request: WikiPageUpdate):
    try:
        updated = wiki_service.update_page(
            page_id=page_id,
            title=request.title,
            content=request.content,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Wiki page not found")
        return {"message": "Wiki page updated successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pages/{page_id}/export")
async def export_page(page_id: str):
    try:
        export = wiki_service.export_page(page_id)
        if not export:
            raise HTTPException(status_code=404, detail="Wiki page not found")
        return export
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate")
async def generate_page(request: WikiPageGenerate):
    try:
        return await wiki_service.generate_page(
            title=request.title,
            source_doc_ids=request.source_doc_ids,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
