from __future__ import annotations

import logging
from typing import Optional

from langchain_core.documents import Document

from src.config import settings
from backend.src.retrieval.vector_retriever import VectorRetriever
from backend.src.retrieval.bm25_retriever import BM25Retriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(
        self,
        dense_retriever: VectorRetriever,
        sparse_retriever: BM25Retriever,
        *,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        rrf_k: int = 60,
    ):
        self._dense_retriever = dense_retriever
        self._bm25_retriever = sparse_retriever
        self._dense_weight = dense_weight if dense_weight is not None else settings.dense_weight
        self._sparse_weight = sparse_weight if sparse_weight is not None else settings.bm25_weight
        self._rrf_k = rrf_k

        total = self._dense_weight + self._sparse_weight
        if total > 0:
            self._dense_weight /= total
            self._sparse_weight /= total

    def retrieve(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        method: str = "rrf",
    ) -> list[tuple[Document, float]]:
        k = top_k or settings.retrieval_top_k

        if method == "rrf":
            return self._rrf_retrieve(query, top_k=k)
        elif method == "weighted":
            return self._weighted_retrieve(query, top_k=k)
        else:
            return self._rrf_retrieve(query, top_k=k)

    def _rrf_retrieve(
        self,
        query: str,
        *,
        top_k: int,
    ) -> list[tuple[Document, float]]:
        dense_results = self._dense_retriever.dense_search(query, top_k=top_k * 2)
        sparse_results = self._bm25_retriever.retrieve(query, top_k=top_k * 2)

        doc_scores: dict[str, tuple[Document, float]] = {}

        for rank, (doc, _score) in enumerate(dense_results, start=1):
            doc_id = doc.metadata.get("_id", doc.page_content[:100])
            rrf_score = self._dense_weight / (self._rrf_k + rank)
            if doc_id in doc_scores:
                doc_scores[doc_id] = (doc, doc_scores[doc_id][1] + rrf_score)
            else:
                doc_scores[doc_id] = (doc, rrf_score)

        for rank, (doc, _score) in enumerate(sparse_results, start=1):
            doc_id = doc.metadata.get("_id", doc.page_content[:100])
            rrf_score = self._sparse_weight / (self._rrf_k + rank)
            if doc_id in doc_scores:
                doc_scores[doc_id] = (doc, doc_scores[doc_id][1] + rrf_score)
            else:
                doc_scores[doc_id] = (doc, rrf_score)

        sorted_results = sorted(doc_scores.values(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def _weighted_retrieve(
        self,
        query: str,
        *,
        top_k: int,
    ) -> list[tuple[Document, float]]:
        dense_results = self._dense_retriever.dense_search(query, top_k=top_k * 2)
        sparse_results = self._bm25_retriever.retrieve(query, top_k=top_k * 2)

        all_scores: dict[str, tuple[Document, float, float]] = {}

        max_dense = max((s for _, s in dense_results), default=1.0)
        max_sparse = max((s for _, s in sparse_results), default=1.0)

        for doc, score in dense_results:
            doc_id = doc.metadata.get("_id", doc.page_content[:100])
            norm_score = score / max_dense if max_dense > 0 else 0
            all_scores[doc_id] = (doc, norm_score, 0.0)

        for doc, score in sparse_results:
            doc_id = doc.metadata.get("_id", doc.page_content[:100])
            norm_score = score / max_sparse if max_sparse > 0 else 0
            if doc_id in all_scores:
                existing_doc, d_score, _ = all_scores[doc_id]
                all_scores[doc_id] = (existing_doc, d_score, norm_score)
            else:
                all_scores[doc_id] = (doc, 0.0, norm_score)

        combined: list[tuple[Document, float]] = []
        for doc_id, (doc, d_score, s_score) in all_scores.items():
            final = self._dense_weight * d_score + self._sparse_weight * s_score
            doc.metadata["_retrieval_method"] = "weighted"
            combined.append((doc, final))

        combined.sort(key=lambda x: x[1], reverse=True)
        return combined[:top_k]