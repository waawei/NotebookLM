"""
文档管理 API 路由
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
from pydantic import BaseModel

from services.document_service import DocumentService
from models.document import DocumentResponse, DocumentListResponse

router = APIRouter()
document_service = DocumentService()


class UploadResponse(BaseModel):
    """上传响应"""
    doc_id: str
    filename: str
    status: str
    message: str


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    上传文档

    支持格式: PDF, TXT, MD, DOCX
    """
    try:
        # 验证文件格式
        allowed_extensions = [".pdf", ".txt", ".md", ".docx"]
        file_ext = "." + file.filename.split(".")[-1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持: {', '.join(allowed_extensions)}"
            )

        # 处理文档上传
        doc_id = await document_service.upload_document(file)

        # 后台任务：向量化文档
        if background_tasks:
            background_tasks.add_task(
                document_service.process_document,
                doc_id
            )

        return UploadResponse(
            doc_id=doc_id,
            filename=file.filename,
            status="processing",
            message="文档上传成功，正在处理中..."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-url", response_model=UploadResponse)
async def upload_url(
    url: str,
    background_tasks: BackgroundTasks = None
):
    """
    上传网页 URL

    支持任意可访问的网页
    """
    try:
        # 处理 URL 上传
        doc_id = await document_service.upload_url(url)

        # 后台任务：抓取和向量化
        if background_tasks:
            background_tasks.add_task(
                document_service.process_url,
                doc_id
            )

        return UploadResponse(
            doc_id=doc_id,
            filename=url,
            status="processing",
            message="网页正在抓取和处理中..."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """
    获取所有文档列表
    """
    try:
        documents = await document_service.list_documents()
        return DocumentListResponse(documents=documents, total=len(documents))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """
    获取单个文档详情
    """
    try:
        document = await document_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    删除文档
    """
    try:
        success = await document_service.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {"message": "文档删除成功", "doc_id": doc_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/status")
async def get_document_status(doc_id: str):
    """
    获取文档处理状态
    """
    try:
        status = await document_service.get_document_status(doc_id)
        if not status:
            raise HTTPException(status_code=404, detail="文档不存在")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
