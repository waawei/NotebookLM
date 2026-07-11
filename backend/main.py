"""
NotebookLM Clone FastAPI entry point.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import agents, chat, documents, modeling, notes, outputs, preview, settings as settings_api, skills, spaces, wiki
from core.config import settings
from services.local_llm_config import LLMConfigurationService
from api.modeling import recovery_service

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
app.include_router(preview.router, prefix="/api/preview", tags=["Preview"])
app.include_router(wiki.router, prefix="/api/wiki", tags=["Wiki"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["Settings"])
app.include_router(spaces.router, prefix="/api/spaces", tags=["Spaces"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(modeling.router, prefix="/api/modeling", tags=["Modeling"])


@app.on_event("startup")
async def startup_event():
    """Log startup configuration and reconcile interrupted modeling workflows."""
    effective_llm = LLMConfigurationService().effective_config()
    print("NotebookLM Clone API starting...")
    print(f"Vector database path: {settings.VECTOR_DB_PATH}")
    print(f"LLM provider: {effective_llm.provider}")
    print(f"LLM model: {effective_llm.model}")
    for recovery in recovery_service.recover_interrupted_projects():
        print(
            "Recovered modeling project "
            f"{recovery['project_id']}: {recovery['recovered_from']} -> "
            f"{recovery['recovered_to']}"
        )


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
    effective_llm = LLMConfigurationService().effective_config()
    return {
        "status": "healthy",
        "database": "connected",
        "llm_provider": effective_llm.provider,
        "llm_model": effective_llm.model,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
