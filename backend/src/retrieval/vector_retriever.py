from __future__ import annotations

import logging
from typing import Optional

from langchain_core.documents import Document
from qdrant_client.models import (
    Filter,
    NamedSparseVector,
    NamedVector,
    SearchParams,
    SearchRequest,
    Prefetch,
    Query,
    SparseVector as QdrantSparseVector,
)

from src.config import settings
from backend.src.embedding.bge_embedding import BGEM3Embedding
from backend.src.ingestion.document_store import DocumentStore

logger = logging.getLogger(__name__)


class VectorRetriever:
    def __init__(
        self,
        document_store: DocumentStore,
        embedding_model: BGEM3Embedding,
        *,
        top_k: Optional[int] = None,
    ):
        self._document_store = document_store
        self._embedding_model = embedding_model
        self._top_k = top_k or settings.retrieval_top_k

    def retrieve(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        filter_conditions: Optional[Filter] = None,
    ) -> list[Document]:
        k = top_k or self._top_k
        dense_vector = self._embedding_model.embed_query(query)
        results = self._document_store.client.search(
            collection_name=self._document_store._collection_name,
            query_vector=NamedVector(
                name=DocumentStore.DENSE_VECTOR_NAME,
                vector=dense_vector,
            ),
            limit=k,
            query_filter=filter_conditions,
            with_payload=True,
        )
        return self._points_to_documents(results)

    def hybrid_search(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
    ) -> list[tuple[Document, float]]:
        k = top_k or self._top_k
        dense_vector = self._embedding_model.embed_query(query)
        _, sparse_vector = self._embedding_model.embed_query_with_sparse(query)

        prefetch_list = [
            Prefetch(
                query=dense_vector,
                using=DocumentStore.DENSE_VECTOR_NAME,
                limit=k * 3,
            ),
        ]
        if sparse_vector:
            sv = QdrantSparseVector(
                indices=list(sparse_vector.keys()),
                values=list(sparse_vector.values()),
            )
            prefetch_list.append(Prefetch(
                query=sv,
                using=DocumentStore.SPARSE_VECTOR_NAME,
                limit=k * 3,
            ))

        results = self._document_store.client.query_points(
            collection_name=self._document_store._collection_name,
            prefetch=prefetch_list,
            query=dense_vector,
            using=DocumentStore.DENSE_VECTOR_NAME,
            limit=k,
            with_payload=True,
        )
        docs_with_scores = []
        for point in results.points:
            doc = self._point_to_document(point)
            score = getattr(point, "score", 0.0) or 0.0
            docs_with_scores.append((doc, score))
        return docs_with_scores

    def dense_search(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        filter_conditions: Optional[Filter] = None,
    ) -> list[tuple[Document, float]]:
        k = top_k or self._top_k
        dense_vector = self._embedding_model.embed_query(query)

        results = self._document_store.client.search(
            collection_name=self._document_store._collection_name,
            query_vector=NamedVector(
                name=DocumentStore.DENSE_VECTOR_NAME,
                vector=dense_vector,
            ),
            limit=k,
            query_filter=filter_conditions,
            with_payload=True,
        )

        docs_with_scores = []
        for point in results:
            doc = self._point_to_document(point)
            docs_with_scores.append((doc, point.score))

        return docs_with_scores

    def sparse_search(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        filter_conditions: Optional[Filter] = None,
    ) -> list[tuple[Document, float]]:
        k = top_k or self._top_k
        _, sparse_vector = self._embedding_model.embed_query_with_sparse(query)

        if not sparse_vector:
            return []

        sv = QdrantSparseVector(indices=list(sparse_vector.keys()), values=list(sparse_vector.values()))

        results = self._document_store.client.search(
            collection_name=self._document_store._collection_name,
            query_vector=NamedSparseVector(
                name=DocumentStore.SPARSE_VECTOR_NAME,
                vector=sv,
            ),
            limit=k,
            query_filter=filter_conditions,
            with_payload=True,
        )

        docs_with_scores = []
        for point in results:
            doc = self._point_to_document(point)
            docs_with_scores.append((doc, point.score))

        return docs_with_scores

    def _points_to_documents(self, points) -> list[Document]:
        return [self._point_to_document(p) for p in points]

    def _point_to_document(self, point) -> Document:
        payload = point.payload or {}
        return Document(
            page_content=payload.get("page_content", ""),
            metadata={
                **payload.get("metadata", {}),
                "_id": str(point.id),
                "_score": getattr(point, "score", None),
            },
        )