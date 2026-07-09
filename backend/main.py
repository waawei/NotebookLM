"""
NotebookLM Clone - FastAPI 主入口
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from api import documents, chat, notes
from services.vector_store import VectorStoreService
from core.config import settings

# 创建 FastAPI 应用
app = FastAPI(
    title="NotebookLM Clone API",
    description="智能文档问答系统",
    version="1.0.0"
)

# 配置 CORS（允许前端跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(documents.router, prefix="/api/documents", tags=["文档管理"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话问答"])
app.include_router(notes.router, prefix="/api/notes", tags=["笔记管理"])


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("🚀 NotebookLM Clone API 启动中...")
    print(f"📊 向量数据库路径: {settings.VECTOR_DB_PATH}")
    print(f"🤖 LLM 提供商: {settings.LLM_PROVIDER}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    print("👋 NotebookLM Clone API 已关闭")


@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "status": "running",
        "message": "NotebookLM Clone API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """详细健康检查"""
    return {
        "status": "healthy",
        "database": "connected",
        "llm_provider": settings.LLM_PROVIDER
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式，代码修改自动重载
    )
