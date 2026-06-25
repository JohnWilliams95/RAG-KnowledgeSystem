from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

from src.config import settings

logger = logging.getLogger(__name__)


class EmbeddingCache:
    def __init__(self, cache_dir: Optional[str] = None):
        self._cache_dir = Path(cache_dir or settings.embedding_cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _make_key(self, text: str) -> str:
        content = f"{settings.embedding_model_name}:{text}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _key_path(self, key: str) -> Path:
        prefix = key[:2]
        subdir = self._cache_dir / prefix
        subdir.mkdir(exist_ok=True)
        return subdir / f"{key}.npy"

    def _meta_path(self, key: str) -> Path:
        prefix = key[:2]
        subdir = self._cache_dir / prefix
        subdir.mkdir(exist_ok=True)
        return subdir / f"{key}.json"

    def get_dense(self, text: str) -> Optional[np.ndarray]:
        key = self._make_key(text)
        path = self._key_path(key)
        if path.exists():
            return np.load(str(path))
        return None

    def get_sparse(self, text: str) -> Optional[dict[str, list]]:
        key = self._make_key(text) + "_sparse"
        path = self._meta_path(key)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data
        return None

    def put_dense(self, text: str, embedding: np.ndarray) -> None:
        key = self._make_key(text)
        path = self._key_path(key)
        np.save(str(path), embedding)

    def put_sparse(self, text: str, sparse_data: dict[str, list]) -> None:
        key = self._make_key(text) + "_sparse"
        path = self._meta_path(key)
        path.write_text(json.dumps(sparse_data, ensure_ascii=False), encoding="utf-8")

    def batch_get_dense(self, texts: list[str]) -> list[Optional[np.ndarray]]:
        return [self.get_dense(t) for t in texts]

    def batch_put_dense(self, texts: list[str], embeddings: np.ndarray) -> None:
        for text, emb in zip(texts, embeddings):
            self.put_dense(text, emb)

    def batch_put_sparse(self, texts: list[str], sparse_data_list: list[dict]) -> None:
        for text, sdata in zip(texts, sparse_data_list):
            self.put_sparse(text, sdata)

    def clear(self) -> None:
        import shutil
        if self._cache_dir.exists():
            shutil.rmtree(self._cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def stats(self) -> dict:
        if not self._cache_dir.exists():
            return {"count": 0, "size_mb": 0}
        count = 0
        total_size = 0
        for f in self._cache_dir.rglob("*.npy"):
            count += 1
            total_size += f.stat().st_size
        return {"count": count, "size_mb": round(total_size / (1024 * 1024), 2)}