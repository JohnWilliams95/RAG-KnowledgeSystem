from __future__ import annotations

import logging
from typing import Optional

from langchain_core.documents import Document
from qdrant_client.models import Filter, NamedSparseVector, SparseVector

from src.config import settings
from src.embedding.bge_embedding import BGEM3Embedding
from src.ingestion.document_store import DocumentStore

logger = logging.getLogger(__name__)


class BM25Retriever:
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
    ) -> list[tuple[Document, float]]:
        k = top_k or self._top_k

        _, sparse_vector = self._embedding_model.embed_query_with_sparse(query)

        if not sparse_vector:
            logger.warning("Empty sparse vector for query, returning no results")
            return []

        indices = list(sparse_vector.keys())
        values = list(sparse_vector.values())

        sv = SparseVector(indices=indices, values=values)
        results = self._document_store.client.search(
            collection_name=self._document_store._collection_name,
            query_vector=NamedSparseVector(
                name=DocumentStore.SPARSE_VECTOR_NAME,
                vector=sv,
            ),
            limit=k,
            with_payload=True,
        )

        docs_with_scores = []
        for point in results:
            payload = point.payload or {}
            doc = Document(
                page_content=payload.get("page_content", ""),
                metadata={
                    **payload.get("metadata", {}),
                    "_id": str(point.id),
                    "_score": point.score,
                    "_search_type": "sparse",
                },
            )
            docs_with_scores.append((doc, point.score))

        return docs_with_scores