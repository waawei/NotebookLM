"""
NotebookLM Clone FastAPI entry point.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import chat, documents, notes, outputs, settings as settings_api, spaces
from core.config import settings

app = FastAPI(
    title="NotebookLM Clone API",
    description="Intelligent document question-answering system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(outputs.router, prefix="/api/outputs", tags=["Outputs"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["Settings"])
app.include_router(spaces.router, prefix="/api/spaces", tags=["Spaces"])


@app.on_event("startup")
async def startup_event():
    """Log startup configuration."""
    print("NotebookLM Clone API starting...")
    print(f"Vector database path: {settings.VECTOR_DB_PATH}")
    print(f"LLM provider: {settings.LLM_PROVIDER}")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown."""
    print("NotebookLM Clone API stopped")


@app.get("/")
async def root():
    """Basic health endpoint."""
    return {
        "status": "running",
        "message": "NotebookLM Clone API is running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Detailed health endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "llm_provider": settings.LLM_PROVIDER,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
