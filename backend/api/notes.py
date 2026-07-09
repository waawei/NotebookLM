"""
笔记管理 API 路由
"""

from fastapi import APIRouter, HTTPException

from models.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
from services.note_service import NoteService

router = APIRouter()
note_service = NoteService()


@router.post("/create", response_model=dict)
async def create_note(request: NoteCreate):
    """
    创建笔记
    """
    try:
        note_id = await note_service.create_note(
            title=request.title,
            content=request.content,
            doc_ids=request.doc_ids,
            conversation_id=request.conversation_id
        )
        return {"note_id": note_id, "message": "Note created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=NoteListResponse)
async def list_notes():
    """
    获取所有笔记列表
    """
    try:
        notes = await note_service.list_notes()
        return NoteListResponse(notes=notes, total=len(notes))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str):
    """
    获取单个笔记详情
    """
    try:
        note = await note_service.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{note_id}", response_model=dict)
async def update_note(note_id: str, request: NoteUpdate):
    """
    更新笔记
    """
    try:
        success = await note_service.update_note(
            note_id=note_id,
            title=request.title,
            content=request.content,
            doc_ids=request.doc_ids,
            conversation_id=request.conversation_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"message": "Note updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{note_id}", response_model=dict)
async def delete_note(note_id: str):
    """
    删除笔记
    """
    try:
        success = await note_service.delete_note(note_id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"message": "Note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
