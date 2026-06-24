from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends

from src.api.schemas.response import (
    RetrievedDocument,
    RetrievalRequest,
    RetrievalResponse,
)
from src.retrieval.ensemble_retriever import EnsembleRetriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retrieval", tags=["retrieval"])

_retriever: Optional[EnsembleRetriever] = None


def get_retriever() -> EnsembleRetriever:
    global _retriever
    if _retriever is None:
        from src.api.dependencies import get_ensemble_retriever
        _retriever = get_ensemble_retriever()
    return _retriever


@router.post("/search", response_model=RetrievalResponse)
async def search(
    request: RetrievalRequest,
    retriever: EnsembleRetriever = Depends(get_retriever),
):
    documents = retriever.retrieve(
        request.query,
        top_k=request.top_k,
        rerank_top_n=request.rerank_top_n,
        rerank_enabled=request.rerank_enabled,
        method=request.method,
    )

    retrieved_docs = []
    for doc in documents:
        retrieved_docs.append(RetrievedDocument(
            page_content=doc.page_content,
            metadata=doc.metadata,
            score=doc.metadata.get("_score"),
            rerank_score=doc.metadata.get("_rerank_score"),
        ))

    return RetrievalResponse(
        query=request.query,
        documents=retrieved_docs,
        total=len(retrieved_docs),
    )


@router.post("/dense")
async def dense_search(
    request: RetrievalRequest,
    retriever: EnsembleRetriever = Depends(get_retriever),
):
    results = retriever.dense_only(request.query, top_k=request.top_k)
    docs = []
    for doc, score in results:
        docs.append({
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "score": score,
        })
    return {"query": request.query, "results": docs, "total": len(docs)}


@router.post("/sparse")
async def sparse_search(
    request: RetrievalRequest,
    retriever: EnsembleRetriever = Depends(get_retriever),
):
    results = retriever.sparse_only(request.query, top_k=request.top_k)
    docs = []
    for doc, score in results:
        docs.append({
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "score": score,
        })
    return {"query": request.query, "results": docs, "total": len(docs)}