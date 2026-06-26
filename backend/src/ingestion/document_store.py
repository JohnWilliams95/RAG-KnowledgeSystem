from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Distance,
    PointStruct,
    SparseVector,
    VectorParams,
    SparseVectorParams,
    HnswConfigDiff,
)

from src.config import settings
from src.embedding.bge_embedding import BGEM3Embedding
from src.embedding.sparse_embedding import SparseEmbedding

logger = logging.getLogger(__name__)


class DocumentStore:
    DENSE_VECTOR_NAME = "dense"
    SPARSE_VECTOR_NAME = "sparse"

    def __init__(
        self,
        embedding_model: BGEM3Embedding,
        sparse_embedding: Optional[SparseEmbedding] = None,
        *,
        collection_name: Optional[str] = None,
    ):
        self._embedding_model = embedding_model
        self._sparse_embedding = sparse_embedding or SparseEmbedding(embedding_model)
        self._collection_name = collection_name or settings.qdrant_collection_name
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> QdrantClient:
        if settings.qdrant_use_memory:
            return QdrantClient(":memory:")

        kwargs: dict = {
            "host": settings.qdrant_host,
            "port": settings.qdrant_port,
            "grpc_port": settings.qdrant_grpc_port,
        }
        if settings.qdrant_api_key:
            kwargs["api_key"] = settings.qdrant_api_key

        return QdrantClient(**kwargs)

    def init_collection(self) -> None:
        if self.client.collection_exists(self._collection_name):
            logger.info(f"Collection '{self._collection_name}' already exists")
            return

        self.client.create_collection(
            collection_name=self._collection_name,
            vectors_config={
                self.DENSE_VECTOR_NAME: VectorParams(
                    size=self._embedding_model.dimension,
                    distance=Distance.COSINE,
                    hnsw_config=HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10000,
                    ),
                ),
            },
            sparse_vectors_config={
                self.SPARSE_VECTOR_NAME: SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False),
                ),
            },
        )
        logger.info(f"Collection '{self._collection_name}' created successfully")

    def add_documents(
        self,
        documents: list[Document],
        *,
        batch_size: int = 64,
    ) -> list[str]:
        self.init_collection()

        texts = [doc.page_content for doc in documents]
        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc.metadata.get('source', '')}:{doc.page_content[:200]}:{i}"))
               for i, doc in enumerate(documents)]

        dense_vectors, sparse_vectors = self._embedding_model.embed_documents_with_sparse(texts)

        for start in range(0, len(documents), batch_size):
            end = min(start + batch_size, len(documents))
            batch_docs = documents[start:end]
            batch_ids = ids[start:end]
            batch_dense = dense_vectors[start:end]
            batch_sparse = sparse_vectors[start:end]

            points = []
            for i, (doc, doc_id, dense, sparse) in enumerate(
                zip(batch_docs, batch_ids, batch_dense, batch_sparse)
            ):
                clean_meta = self._clean_metadata(doc.metadata)
                sparse_vec = SparseVector(
                    indices=list(sparse.keys()),
                    values=list(sparse.values()),
                ) if sparse else SparseVector(indices=[], values=[])
                point = PointStruct(
                    id=doc_id,
                    vector={
                        self.DENSE_VECTOR_NAME: dense,
                        self.SPARSE_VECTOR_NAME: sparse_vec,
                    },
                    payload={
                        "page_content": doc.page_content,
                        "metadata": clean_meta,
                    },
                )
                points.append(point)

            self.client.upsert(
                collection_name=self._collection_name,
                points=points,
            )
            logger.info(f"Upserted batch {start // batch_size + 1}: {len(points)} points")

        logger.info(f"Total {len(ids)} documents added to collection '{self._collection_name}'")
        return ids

    def add_documents_with_embeddings(
        self,
        documents: list[Document],
        dense_vectors: list[list[float]],
        sparse_vectors: list[dict[int, float]],
        *,
        batch_size: int = 64,
    ) -> list[str]:
        self.init_collection()

        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc.metadata.get('source', '')}:{doc.page_content[:200]}:{i}"))
               for i, doc in enumerate(documents)]

        for start in range(0, len(documents), batch_size):
            end = min(start + batch_size, len(documents))
            batch_docs = documents[start:end]
            batch_ids = ids[start:end]
            batch_dense = dense_vectors[start:end]
            batch_sparse = sparse_vectors[start:end]

            points = []
            for doc, doc_id, dense, sparse in zip(
                batch_docs, batch_ids, batch_dense, batch_sparse
            ):
                clean_meta = self._clean_metadata(doc.metadata)
                sparse_vec = SparseVector(
                    indices=list(sparse.keys()),
                    values=list(sparse.values()),
                ) if sparse else SparseVector(indices=[], values=[])
                point = PointStruct(
                    id=doc_id,
                    vector={
                        self.DENSE_VECTOR_NAME: dense,
                        self.SPARSE_VECTOR_NAME: sparse_vec,
                    },
                    payload={
                        "page_content": doc.page_content,
                        "metadata": clean_meta,
                    },
                )
                points.append(point)

            self.client.upsert(
                collection_name=self._collection_name,
                points=points,
            )

        return ids

    def delete_documents(self, ids: list[str]) -> None:
        from qdrant_client.models import PointIdsList

        self.client.delete(
            collection_name=self._collection_name,
            points_selector=PointIdsList(points=ids),
        )
        logger.info(f"Deleted {len(ids)} documents from '{self._collection_name}'")

    def delete_by_filter(self, field: str, value: str) -> dict:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        count_before = self.client.count(
            collection_name=self._collection_name,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key=f"metadata.{field}",
                        match=MatchValue(value=value),
                    )
                ]
            ),
        ).count

        self.client.delete(
            collection_name=self._collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key=f"metadata.{field}",
                        match=MatchValue(value=value),
                    )
                ]
            ),
        )
        logger.info(f"Deleted {count_before} documents where metadata.{field}={value}")
        return {"deleted": count_before}

    def get_collection_info(self) -> dict:
        if not self.client.collection_exists(self._collection_name):
            return {"exists": False}
        info = self.client.get_collection(self._collection_name)
        result = {
            "exists": True,
            "points_count": info.points_count,
            "status": str(info.status),
        }
        # 新版 qdrant-client 可能移除了 vectors_count 属性
        if hasattr(info, "vectors_count"):
            result["vectors_count"] = info.vectors_count
        return result

    def _clean_metadata(self, metadata: dict) -> dict:
        clean = {}
        for k, v in metadata.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif isinstance(v, list):
                clean[k] = [str(item) if not isinstance(item, (str, int, float, bool)) else item for item in v]
            elif isinstance(v, dict):
                import json
                clean[k] = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, Path):
                clean[k] = str(v)
            else:
                clean[k] = str(v)
        return clean