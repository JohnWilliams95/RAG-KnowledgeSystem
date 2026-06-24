from __future__ import annotations

import logging
from typing import Optional

from langchain_core.documents import Document

from src.config import settings
from src.embedding.bge_embedding import BGEM3Embedding
from src.ingestion.document_store import DocumentStore
from src.retrieval.vector_retriever import VectorRetriever
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.reranker import Reranker

logger = logging.getLogger(__name__)


class EnsembleRetriever:
    def __init__(
        self,
        document_store: DocumentStore,
        embedding_model: BGEM3Embedding,
        *,
        top_k: Optional[int] = None,
        rerank_top_n: Optional[int] = None,
        rerank_threshold: float = 0.3,
        rerank_enabled: bool = True,
        hybrid_method: str = "rrf",
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        rrf_k: int = 60,
    ):
        self._document_store = document_store
        self._embedding_model = embedding_model

        self._dense_retriever = VectorRetriever(
            document_store=document_store,
            embedding_model=embedding_model,
            top_k=top_k,
        )
        self._sparse_retriever = BM25Retriever(
            document_store=document_store,
            embedding_model=embedding_model,
            top_k=top_k,
        )
        self._hybrid_retriever = HybridRetriever(
            dense_retriever=self._dense_retriever,
            sparse_retriever=self._sparse_retriever,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
            rrf_k=rrf_k,
        )

        self._reranker = Reranker(top_n=rerank_top_n)
        self._rerank_enabled = rerank_enabled
        self._rerank_threshold = rerank_threshold
        self._hybrid_method = hybrid_method
        self._top_k = top_k or settings.retrieval_top_k
        self._rerank_top_n = rerank_top_n or settings.rerank_top_n

    def retrieve(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        rerank_top_n: Optional[int] = None,
        rerank_enabled: Optional[bool] = None,
        method: Optional[str] = None,
    ) -> list[Document]:
        k = top_k or self._top_k
        n = rerank_top_n or self._rerank_top_n
        use_rerank = rerank_enabled if rerank_enabled is not None else self._rerank_enabled
        hybrid_method = method or self._hybrid_method

        hybrid_results = self._hybrid_retriever.retrieve(
            query, top_k=k, method=hybrid_method
        )

        logger.info(f"Hybrid retrieval returned {len(hybrid_results)} candidates")

        if not use_rerank:
            return [doc for doc, _ in hybrid_results[:n]]

        reranked = self._reranker.rerank(query, [doc for doc, _ in hybrid_results], top_n=n)
        reranked = self._reranker.filter_by_threshold(reranked, threshold=self._rerank_threshold)

        logger.info(f"Reranked to {len(reranked)} results (threshold={self._rerank_threshold})")
        return [doc for doc, _ in reranked]

    def retrieve_with_scores(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        rerank_top_n: Optional[int] = None,
    ) -> list[tuple[Document, float]]:
        k = top_k or self._top_k
        n = rerank_top_n or self._rerank_top_n

        hybrid_results = self._hybrid_retriever.retrieve(query, top_k=k, method=self._hybrid_method)

        if not self._rerank_enabled:
            return hybrid_results[:n]

        reranked = self._reranker.rerank(query, [doc for doc, _ in hybrid_results], top_n=n)
        return reranked

    def dense_only(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
    ) -> list[tuple[Document, float]]:
        k = top_k or self._top_k
        return self._dense_retriever.dense_search(query, top_k=k)

    def sparse_only(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
    ) -> list[tuple[Document, float]]:
        k = top_k or self._top_k
        return self._sparse_retriever.retrieve(query, top_k=k)