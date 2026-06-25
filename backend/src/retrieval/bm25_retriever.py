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
    ):
        self._top_k = top_k or settings.retrieval_top_k
        self._cache_dir = Path(cache_dir or settings.embedding_cache_dir).parent / "bm25"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._bm25 = None
        self._corpus_docs: list[Document] = []
        self._tokenized_corpus: list[list[str]] = []
        self._collection_name: Optional[str] = None

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
            logger.warning("BM25 index not built. Call build_index() first.")
            return

        self._bm25 = BM25Okapi(self._tokenized_corpus)

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