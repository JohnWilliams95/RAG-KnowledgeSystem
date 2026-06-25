from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.src.api.routes import chat, document, knowledge_base
from src.config import settings
from backend.src.api.routes import retrieval
from backend.src.middleware.trace import TraceMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG-Langchain-v2 API starting up...")
    settings.ensure_directories()
    yield
    logger.info("RAG-Langchain-v2 API shutting down...")


app = FastAPI(
    title="RAG-Langchain-v2",
    description="Production-ready RAG system with LangChain, Qdrant, and BGE-M3",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(TraceMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(document.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(retrieval.router, prefix="/api/v1")
app.include_router(knowledge_base.router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root():
    return {
        "name": "RAG-Langchain-v2",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    try:
        from backend.src.api.dependencies import get_document_store
        ds = get_document_store()
        info = ds.get_collection_info()
        return {
            "status": "healthy",
            "version": "0.1.0",
            "qdrant_connected": info.get("exists", False),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "version": "0.1.0",
            "qdrant_connected": False,
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )