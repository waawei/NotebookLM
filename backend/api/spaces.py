"""
Source space API routes.
"""

from fastapi import APIRouter, HTTPException

from models.document import SpaceCreate, SpaceResponse, SpaceUpdate
from services.document_metadata_store import DocumentMetadataStore

router = APIRouter()
metadata_store = DocumentMetadataStore()


@router.get("")
async def list_spaces():
    return {"spaces": metadata_store.list_spaces()}


@router.post("", response_model=SpaceResponse)
async def create_space(request: SpaceCreate):
    return metadata_store.create_space(request.name, request.description)


@router.put("/{space_id}", response_model=SpaceResponse)
async def update_space(space_id: str, request: SpaceUpdate):
    space = metadata_store.update_space(
        space_id=space_id,
        name=request.name,
        description=request.description,
    )
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space


@router.delete("/{space_id}")
async def delete_space(space_id: str):
    deleted = metadata_store.delete_space(space_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Space not found")
    return {"message": "Space deleted successfully", "space_id": space_id}


@router.post("/{space_id}/documents/{doc_id}")
async def assign_document_to_space(space_id: str, doc_id: str):
    if not metadata_store.get_space(space_id):
        raise HTTPException(status_code=404, detail="Space not found")
    if not metadata_store.get_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")

    metadata_store.assign_document_to_space(doc_id, space_id)
    return {"message": "Document assigned to space", "space_id": space_id, "doc_id": doc_id}
