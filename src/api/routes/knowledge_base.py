from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter

from src.api.schemas.response import KnowledgeBaseInfo
from src.config import settings
from src.ingestion.document_store import DocumentStore
from src.ingestion.metadata_store import MetadataStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.get("/info", response_model=KnowledgeBaseInfo)
async def get_knowledge_base_info():
    from src.api.dependencies import get_document_store, get_metadata_store
    ds = get_document_store()
    info = ds.get_collection_info()
    return KnowledgeBaseInfo(
        collection_name=settings.qdrant_collection_name,
        exists=info.get("exists", False),
        points_count=info.get("points_count"),
        vectors_count=info.get("vectors_count"),
        status=info.get("status"),
    )


@router.get("/documents")
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
):
    from src.api.dependencies import get_metadata_store
    ms = get_metadata_store()
    docs = ms.list_documents(status=status, limit=limit, offset=offset)
    return {"documents": docs, "total": len(docs)}


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    from src.api.dependencies import get_metadata_store
    ms = get_metadata_store()
    doc = ms.get_document(doc_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/init")
async def init_collection():
    from src.api.dependencies import get_document_store
    ds = get_document_store()
    ds.init_collection()
    return {"status": "success", "message": f"Collection '{settings.qdrant_collection_name}' initialized"}


@router.get("/stats")
async def get_stats():
    from src.api.dependencies import get_document_store, get_metadata_store
    ds = get_document_store()
    ms = get_metadata_store()
    info = ds.get_collection_info()
    conn = ms._get_conn()
    total = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]
    return {
        "collection": info,
        "total_documents": total,
    }