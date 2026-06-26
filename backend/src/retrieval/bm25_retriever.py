from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from langchain_core.documents import Document

from src.config import settings

logger = logging.getLogger(__name__)


class BM25Retriever:
    def __init__(
        self,
        *,
        top_k: Optional[int] = None,
        cache_dir: Optional[str] = None,
        document_store=None,
    ):
        self._top_k = top_k or settings.retrieval_top_k
        self._cache_dir = Path(cache_dir or settings.embedding_cache_dir).parent / "bm25"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._bm25 = None
        self._corpus_docs: list[Document] = []
        self._tokenized_corpus: list[list[str]] = []
        self._collection_name: Optional[str] = None
        self._document_store = document_store

    def _init_bm25(self):
        if self._bm25 is not None:
            return
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.error("rank_bm25 not installed. Install with: pip install rank_bm25")
            raise

        cache_file = self._cache_dir / f"{self._collection_name or 'default'}.pkl"
        if cache_file.exists():
            data = pickle.loads(cache_file.read_bytes())
            self._corpus_docs = data["docs"]
            self._tokenized_corpus = data["tokens"]
            logger.info(f"BM25 index loaded from cache: {len(self._corpus_docs)} documents")
        else:
            # 如果没有缓存且有 document store，自动构建索引
            if self._document_store:
                logger.info("BM25 cache not found, building index from document store...")
                self._build_index_from_store()
            else:
                logger.warning("BM25 index not built. Call build_index() first.")
                return

        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)
        else:
            logger.warning("BM25 index is empty")

    def _build_index_from_store(self):
        """从 document store 自动构建 BM25 索引"""
        try:
            from src.api.dependencies import get_metadata_store, get_document_store
            
            ms = get_metadata_store()
            ds = get_document_store()
            conn = ms._get_conn()
            
            # 获取所有已完成文档的 chunks
            rows = conn.execute("""
                SELECT c.chunk_id, c.doc_id, c.chunk_index, c.qdrant_point_id,
                       c.metadata, d.file_name, d.file_type
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
                WHERE d.status = 'completed' AND c.qdrant_point_id IS NOT NULL
                ORDER BY d.file_name, c.chunk_index
            """).fetchall()
            
            if not rows:
                logger.info("No documents found in database for BM25 index")
                return
            
            # 从 Qdrant 批量获取文档内容
            point_ids = [row["qdrant_point_id"] for row in rows]
            
            try:
                # 使用 Qdrant 的 retrieve 方法获取文档内容
                points = ds.client.retrieve(
                    collection_name=settings.qdrant_collection_name,
                    ids=point_ids,
                    with_payload=True,
                )
                
                # 创建 point_id -> payload 的映射
                payload_map = {str(p.id): p.payload for p in points}
                
                docs = []
                for row in rows:
                    point_id = row["qdrant_point_id"]
                    payload = payload_map.get(point_id, {})
                    page_content = payload.get("page_content", "")
                    
                    if not page_content:
                        continue
                    
                    import json
                    meta = json.loads(row["metadata"]) if row["metadata"] else {}
                    meta["source"] = row["file_name"]
                    meta["file_type"] = row["file_type"]
                    meta["doc_id"] = row["doc_id"]
                    meta["chunk_index"] = row["chunk_index"]
                    
                    docs.append(Document(
                        page_content=page_content,
                        metadata=meta
                    ))
                
                if docs:
                    self.build_index(docs, collection_name=settings.qdrant_collection_name)
                    logger.info(f"Auto-built BM25 index with {len(docs)} chunks")
                
            except Exception as e:
                logger.error(f"Failed to fetch documents from Qdrant: {e}")
            
        except Exception as e:
            logger.error(f"Failed to auto-build BM25 index: {e}", exc_info=True)

    def build_index(
        self,
        documents: list[Document],
        *,
        collection_name: Optional[str] = None,
    ) -> None:
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.error("rank_bm25 not installed")
            return

        self._collection_name = collection_name
        self._corpus_docs = documents
        self._tokenized_corpus = [self._tokenize(doc.page_content) for doc in documents]
        self._bm25 = BM25Okapi(self._tokenized_corpus)

        cache_file = self._cache_dir / f"{collection_name or 'default'}.pkl"
        cache_file.write_bytes(pickle.dumps({
            "docs": documents,
            "tokens": self._tokenized_corpus,
        }))
        logger.info(f"BM25 index built with {len(documents)} documents, saved to {cache_file}")

    def add_documents(self, documents: list[Document]) -> None:
        self._corpus_docs.extend(documents)
        new_tokens = [self._tokenize(doc.page_content) for doc in documents]
        self._tokenized_corpus.extend(new_tokens)

        try:
            from rank_bm25 import BM25Okapi
            self._bm25 = BM25Okapi(self._tokenized_corpus)
        except ImportError:
            logger.error("rank_bm25 not installed")
            return

        cache_file = self._cache_dir / f"{self._collection_name or 'default'}.pkl"
        cache_file.write_bytes(pickle.dumps({
            "docs": self._corpus_docs,
            "tokens": self._tokenized_corpus,
        }))

    def retrieve(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
    ) -> list[tuple[Document, float]]:
        self._init_bm25()
        if self._bm25 is None:
            return []

        k = top_k or self._top_k
        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        top_indices = np.argsort(scores)[::-1][:k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self._corpus_docs[idx]
                doc_copy = Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "_score": float(scores[idx]), "_search_type": "bm25"},
                )
                results.append((doc_copy, float(scores[idx])))

        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re
        text = text.lower()
        tokens = re.findall(r'[\w\u4e00-\u9fff]+', text)
        return tokens