"""
向量存储服务 - 使用 ChromaDB
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Optional

from core.config import settings


class VectorStoreService:
    """向量数据库服务"""

    def __init__(self):
        # 初始化 ChromaDB 客户端
        self.client = chromadb.Client(ChromaSettings(
            persist_directory=settings.VECTOR_DB_PATH,
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True
        ))

        # 初始化 Embedding 模型
        self.embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )

        # 创建或获取集合
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "文档向量存储"}
        )

    async def add_documents(self, doc_id: str, chunks: List[str]) -> bool:
        """
        添加文档到向量数据库

        Args:
            doc_id: 文档 ID
            chunks: 文档分块列表

        Returns:
            success: 是否成功
        """
        try:
            # 生成向量
            embeddings = self.embedding_model.encode(chunks).tolist()

            # 准备 ID 和元数据
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "doc_id": doc_id,
                    "chunk_id": i,
                    "chunk_size": len(chunk)
                }
                for i, chunk in enumerate(chunks)
            ]

            # 存入 ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )

            return True

        except Exception as e:
            print(f"向量化存储失败: {e}")
            raise e

    async def search(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = None
    ) -> List[dict]:
        """
        搜索相关文档块

        Args:
            query: 查询文本
            doc_ids: 限制搜索的文档 ID 列表
            top_k: 返回的结果数量

        Returns:
            results: 搜索结果列表
        """
        if top_k is None:
            top_k = settings.TOP_K_RESULTS

        # 向量化查询
        query_embedding = self.embedding_model.encode([query]).tolist()

        # 构建过滤条件
        where = None
        if doc_ids:
            where = {"doc_id": {"$in": doc_ids}}

        # 搜索
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where
        )

        # 格式化结果
        formatted_results = []
        if results["documents"] and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],  # 转换为相似度分数
                    "id": results["ids"][0][i]
                })

        return formatted_results

    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档的所有向量

        Args:
            doc_id: 文档 ID

        Returns:
            success: 是否成功
        """
        try:
            # 查找该文档的所有 chunk
            results = self.collection.get(
                where={"doc_id": doc_id}
            )

            if results["ids"]:
                # 删除所有相关向量
                self.collection.delete(ids=results["ids"])

            return True

        except Exception as e:
            print(f"删除文档向量失败: {e}")
            return False
