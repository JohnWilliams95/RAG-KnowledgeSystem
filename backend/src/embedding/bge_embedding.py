from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from langchain_core.embeddings import Embeddings

from src.config import settings
from src.embedding.embedding_cache import EmbeddingCache

logger = logging.getLogger(__name__)


class BGEM3Embedding(Embeddings):
    def __init__(
        self,
        *,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        use_fp16: Optional[bool] = None,
        batch_size: Optional[int] = None,
        use_cache: bool = True,
    ):
        self._model_name = model_name or settings.embedding_model_name
        self._device = device or settings.embedding_device
        self._use_fp16 = use_fp16 if use_fp16 is not None else settings.embedding_use_fp16
        self._batch_size = batch_size or settings.embedding_batch_size
        self._use_cache = use_cache

        self._model = None
        self._cache = EmbeddingCache() if use_cache else None
        self._dimension: Optional[int] = None

    def _init_model(self):
        if self._model is not None:
            return
        from FlagEmbedding import BGEM3FlagModel

        logger.info(f"Loading BGE-M3 model: {self._model_name} on {self._device}")
        self._model = BGEM3FlagModel(
            self._model_name,
            use_fp16=self._use_fp16,
            device=self._device,
        )
        logger.info("BGE-M3 model loaded successfully")

        if self._dimension is None:
            test_output = self._model.encode(["test"], batch_size=1)
            if isinstance(test_output, dict) and "dense_vecs" in test_output:
                self._dimension = len(test_output["dense_vecs"][0])
            elif isinstance(test_output, dict) and "dense_embeds" in test_output:
                self._dimension = len(test_output["dense_embeds"][0])
            else:
                self._dimension = len(test_output[0])
            logger.info(f"Detected embedding dimension: {self._dimension}")

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._init_model()
        return self._dimension or 1024

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_batch(texts, is_query=False)

    def embed_query(self, text: str) -> list[float]:
        results = self._embed_batch([text], is_query=True)
        return results[0]

    def _embed_batch(self, texts: list[str], is_query: bool = False) -> list[list[float]]:
        self._init_model()

        all_embeddings: list[list[float]] = []
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        if self._cache and not is_query:
            cached = self._cache.batch_get_dense(texts)
            for i, emb in enumerate(cached):
                if emb is not None:
                    all_embeddings.append(emb.tolist())
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(texts[i])
                    all_embeddings.append(None)
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts
            all_embeddings = [None] * len(texts)

        if uncached_texts:
            new_embeddings = self._compute_dense(uncached_texts)
            for idx_in_uncached, idx_in_all in enumerate(uncached_indices):
                all_embeddings[idx_in_all] = new_embeddings[idx_in_uncached].tolist()

            if self._cache and not is_query:
                self._cache.batch_put_dense(uncached_texts, new_embeddings)

        for i, emb in enumerate(all_embeddings):
            if emb is None:
                all_embeddings[i] = [0.0] * self.dimension

        return all_embeddings

    def _compute_dense(self, texts: list[str]) -> np.ndarray:
        output = self._model.encode(texts, batch_size=self._batch_size, return_dense=True)
        if isinstance(output, dict):
            # BGEM3FlagModel 使用 'dense_vecs' 键
            if "dense_vecs" in output:
                return output["dense_vecs"]
            elif "dense_embeds" in output:
                return output["dense_embeds"]
        return output

    def embed_documents_with_sparse(
        self, texts: list[str]
    ) -> tuple[list[list[float]], list[dict[int, float]]]:
        self._init_model()

        output = self._model.encode(
            texts,
            batch_size=self._batch_size,
            return_dense=True,
            return_sparse=True,
        )

        if isinstance(output, dict):
            # 处理稠密向量
            if "dense_vecs" in output:
                dense = output["dense_vecs"]
            elif "dense_embeds" in output:
                dense = output["dense_embeds"]
            else:
                dense = []
            dense_list = dense if isinstance(dense, list) else dense.tolist()

            # 处理稀疏向量
            sparse_vectors: list[dict[int, float]] = []
            if "lexical_weights" in output:
                for sparse_emb in output["lexical_weights"]:
                    sparse_dict = {}
                    for token_id, weight in sparse_emb.items():
                        if weight > 0:
                            sparse_dict[int(token_id)] = float(weight)
                    sparse_vectors.append(sparse_dict)
            else:
                sparse_vectors = [{} for _ in texts]
        else:
            dense_list = output if isinstance(output, list) else output.tolist()
            sparse_vectors = [{} for _ in texts]

        return dense_list, sparse_vectors

    def embed_query_with_sparse(
        self, text: str
    ) -> tuple[list[float], dict[int, float]]:
        dense, sparse = self.embed_documents_with_sparse([text])
        return dense[0], sparse[0]