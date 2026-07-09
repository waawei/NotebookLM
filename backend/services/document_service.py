"""
文档服务 - 处理文档上传、解析、向量化
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile

from core.config import settings
from models.document import DocumentMetadata, DocumentResponse
from services.document_parser import DocumentParser
from services.vector_store import VectorStoreService
from services.llm_service import LLMService


class DocumentService:
    """文档管理服务"""

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.parser = DocumentParser()
        self.vector_store = VectorStoreService()
        self.llm_service = LLMService()
        self.documents_meta = {}  # 简单的内存存储，生产环境应使用数据库

        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_document(self, file: UploadFile) -> str:
        """
        上传文档并保存到本地

        Args:
            file: 上传的文件对象

        Returns:
            doc_id: 文档唯一标识
        """
        # 生成唯一文档 ID
        doc_id = str(uuid.uuid4())

        # 保存文件
        file_path = os.path.join(self.upload_dir, f"{doc_id}_{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 保存元数据
        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=file.filename,
            file_type=file.filename.split(".")[-1].lower(),
            file_size=len(content),
            upload_time=datetime.now(),
            status="pending"
        )

        self.documents_meta[doc_id] = {
            "metadata": metadata,
            "file_path": file_path
        }

        return doc_id

    async def upload_url(self, url: str) -> str:
        """
        上传网页 URL

        Args:
            url: 网页 URL

        Returns:
            doc_id: 文档唯一标识
        """
        # 生成唯一文档 ID
        doc_id = str(uuid.uuid4())

        # 保存元数据
        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=url,
            file_type="url",
            file_size=0,
            upload_time=datetime.now(),
            status="pending"
        )

        self.documents_meta[doc_id] = {
            "metadata": metadata,
            "url": url
        }

        return doc_id

    async def process_url(self, doc_id: str) -> bool:
        """
        处理网页 URL：抓取、分块、向量化、生成摘要

        Args:
            doc_id: 文档 ID

        Returns:
            success: 是否成功
        """
        try:
            doc_info = self.documents_meta.get(doc_id)
            if not doc_info:
                raise ValueError(f"文档 {doc_id} 不存在")

            # 更新状态
            doc_info["metadata"].status = "processing"

            # 抓取网页内容
            url = doc_info["url"]
            text = self.parser.parse_url(url)

            # 分块
            chunks = self.parser.chunk_text(text)

            # 向量化并存储
            await self.vector_store.add_documents(doc_id, chunks)

            # 生成文档摘要
            summary = await self._generate_summary(text)

            # 更新元数据
            doc_info["metadata"].status = "completed"
            doc_info["metadata"].total_chunks = len(chunks)
            doc_info["metadata"].summary = summary

            return True

        except Exception as e:
            # 处理失败
            if doc_id in self.documents_meta:
                self.documents_meta[doc_id]["metadata"].status = "failed"
                self.documents_meta[doc_id]["metadata"].error_message = str(e)
            raise e

    async def process_document(self, doc_id: str) -> bool:
        """
        处理文档：解析、分块、向量化、生成摘要

        Args:
            doc_id: 文档 ID

        Returns:
            success: 是否成功
        """
        try:
            doc_info = self.documents_meta.get(doc_id)
            if not doc_info:
                raise ValueError(f"文档 {doc_id} 不存在")

            # 更新状态
            doc_info["metadata"].status = "processing"

            # 解析文档
            file_path = doc_info["file_path"]
            text = self.parser.parse_file(file_path)

            # 分块
            chunks = self.parser.chunk_text(text)

            # 向量化并存储
            await self.vector_store.add_documents(doc_id, chunks)

            # 生成文档摘要
            summary = await self._generate_summary(text)

            # 更新元数据
            doc_info["metadata"].status = "completed"
            doc_info["metadata"].total_chunks = len(chunks)
            doc_info["metadata"].summary = summary

            return True

        except Exception as e:
            # 处理失败
            if doc_id in self.documents_meta:
                self.documents_meta[doc_id]["metadata"].status = "failed"
                self.documents_meta[doc_id]["metadata"].error_message = str(e)
            raise e

    async def _generate_summary(self, text: str) -> str:
        """
        生成文档摘要

        Args:
            text: 文档全文

        Returns:
            summary: 2-3 句话的摘要
        """
        try:
            # 取文档前 2000 字符生成摘要
            content_sample = text[:2000]

            prompt = f"""Summarize the following document in 2-3 sentences. Focus on the main topic and key points.

Document content:
{content_sample}

Summary (2-3 sentences):"""

            summary = await self.llm_service.generate(prompt)
            return summary.strip()

        except Exception as e:
            print(f"Failed to generate summary: {e}")
            return "Summary generation failed."

    async def list_documents(self) -> List[DocumentResponse]:
        """
        获取所有文档列表

        Returns:
            documents: 文档列表
        """
        documents = []
        for doc_info in self.documents_meta.values():
            meta = doc_info["metadata"]
            documents.append(
                DocumentResponse(
                    doc_id=meta.doc_id,
                    filename=meta.filename,
                    file_type=meta.file_type,
                    upload_time=meta.upload_time,
                    status=meta.status,
                    total_chunks=meta.total_chunks,
                    summary=meta.summary
                )
            )
        return documents

    async def get_document(self, doc_id: str) -> Optional[DocumentResponse]:
        """
        获取单个文档详情

        Args:
            doc_id: 文档 ID

        Returns:
            document: 文档信息
        """
        doc_info = self.documents_meta.get(doc_id)
        if not doc_info:
            return None

        meta = doc_info["metadata"]
        return DocumentResponse(
            doc_id=meta.doc_id,
            filename=meta.filename,
            file_type=meta.file_type,
            upload_time=meta.upload_time,
            status=meta.status,
            total_chunks=meta.total_chunks,
            summary=meta.summary
        )

    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档

        Args:
            doc_id: 文档 ID

        Returns:
            success: 是否成功
        """
        doc_info = self.documents_meta.get(doc_id)
        if not doc_info:
            return False

        # 删除文件
        file_path = doc_info["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)

        # 从向量数据库删除
        await self.vector_store.delete_document(doc_id)

        # 删除元数据
        del self.documents_meta[doc_id]

        return True

    async def get_document_status(self, doc_id: str) -> Optional[dict]:
        """
        获取文档处理状态

        Args:
            doc_id: 文档 ID

        Returns:
            status: 状态信息
        """
        doc_info = self.documents_meta.get(doc_id)
        if not doc_info:
            return None

        meta = doc_info["metadata"]
        return {
            "doc_id": doc_id,
            "status": meta.status,
            "total_chunks": meta.total_chunks,
            "error_message": meta.error_message
        }
