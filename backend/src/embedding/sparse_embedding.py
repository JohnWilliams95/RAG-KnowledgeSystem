from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from src.config import settings
from backend.src.embedding.bge_embedding import BGEM3Embedding

logger = logging.getLogger(__name__)


class SparseEmbedding:
    def __init__(self, embedding_model: Optional[BGEM3Embedding] = None):
        self._model = embedding_model
        self._tokenizer = None

    def _init_tokenizer(self):
        if self._tokenizer is not None:
            return
        if self._model and self._model._model:
            self._tokenizer = self._model._model.tokenizer
        else:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(
                settings.embedding_model_name
            )
        logger.info("Sparse embedding tokenizer initialized")

    def encode_sparse(self, texts: list[str]) -> list[dict[int, float]]:
        if self._model and self._model._model:
            _, sparse_vecs = self._model.embed_documents_with_sparse(texts)
            return sparse_vecs
        return self._bm25_style_encode(texts)

    def encode_query_sparse(self, text: str) -> dict[int, float]:
        results = self.encode_sparse([text])
        return results[0] if results else {}

    def _bm25_style_encode(self, texts: list[str]) -> list[dict[int, float]]:
        import math
        from collections import Counter

        self._init_tokenizer()

        all_token_counts: list[Counter] = []
        df: dict[int, int] = {}

        for text in texts:
            tokens = self._tokenizer.encode(text, add_special_tokens=False)
            counts = Counter(tokens)
            all_token_counts.append(counts)
            for token_id in counts:
                df[token_id] = df.get(token_id, 0) + 1

        n_docs = len(texts)
        avg_dl = sum(sum(c.values()) for c in all_token_counts) / max(n_docs, 1)
        k1 = 1.5
        b = 0.75

        sparse_vectors: list[dict[int, float]] = []
        for counts in all_token_counts:
            dl = sum(counts.values())
            vec: dict[int, float] = {}
            for token_id, tf in counts.items():
                idf = math.log((n_docs - df.get(token_id, 0) + 0.5) / (df.get(token_id, 0) + 0.5) + 1)
                tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
                score = idf * tf_norm
                if score > 0:
                    vec[token_id] = float(score)
            sparse_vectors.append(vec)

        return sparse_vectors