from __future__ import annotations

import logging
from typing import Optional

from langchain_core.documents import Document

from src.config import settings

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(
        self,
        *,
        model_name: Optional[str] = None,
        device: str = "cpu",
        use_fp16: bool = False,
        top_n: Optional[int] = None,
    ):
        self._model_name = model_name or settings.reranker_model
        self._device = device
        self._use_fp16 = use_fp16
        self._top_n = top_n or settings.rerank_top_n
        self._model = None

    def _init_model(self):
        if self._model is not None:
            return
        from FlagEmbedding import FlagReranker

        logger.info(f"Loading reranker model: {self._model_name}")
        self._model = FlagReranker(
            self._model_name,
            use_fp16=self._use_fp16,
            devices=self._device,
        )
        logger.info("Reranker model loaded successfully")

    def rerank(
        self,
        query: str,
        documents: list[Document],
        *,
        top_n: Optional[int] = None,
        return_scores: bool = True,
    ) -> list[tuple[Document, float]]:
        if not documents:
            return []

        n = top_n or self._top_n
        self._init_model()

        pairs = [(query, doc.page_content) for doc in documents]

        scores = self._model.compute_score(pairs, normalize=True)

        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        doc_scores: list[tuple[Document, float]] = []
        for doc, score in zip(documents, scores):
            doc.metadata["_rerank_score"] = float(score)
            doc_scores.append((doc, float(score)))

        doc_scores.sort(key=lambda x: x[1], reverse=True)

        return doc_scores[:n]

    def rerank_texts(
        self,
        query: str,
        texts: list[str],
        *,
        top_n: Optional[int] = None,
    ) -> list[tuple[str, float]]:
        if not texts:
            return []

        n = top_n or self._top_n
        self._init_model()

        pairs = [(query, text) for text in texts]
        scores = self._model.compute_score(pairs, normalize=True)

        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        text_scores = list(zip(texts, [float(s) for s in scores]))
        text_scores.sort(key=lambda x: x[1], reverse=True)

        return text_scores[:n]

    def filter_by_threshold(
        self,
        results: list[tuple[Document, float]],
        *,
        threshold: float = 0.3,
    ) -> list[tuple[Document, float]]:
        return [(doc, score) for doc, score in results if score >= threshold]