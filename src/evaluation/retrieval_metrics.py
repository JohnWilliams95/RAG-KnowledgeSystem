from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RetrievalMetrics:
    @staticmethod
    def hit_rate(
        retrieved_ids: list[str],
        relevant_ids: list[str],
    ) -> float:
        if not relevant_ids:
            return 0.0
        hit_set = set(retrieved_ids) & set(relevant_ids)
        return len(hit_set) / len(relevant_ids)

    @staticmethod
    def mrr(
        retrieved_ids: list[str],
        relevant_ids: list[str],
    ) -> float:
        relevant_set = set(relevant_ids)
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_set:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def ndcg(
        retrieved_ids: list[str],
        relevant_ids: list[str],
        *,
        k: Optional[int] = None,
    ) -> float:
        import math

        if not relevant_ids:
            return 0.0

        ids = retrieved_ids[:k] if k else retrieved_ids
        relevant_set = set(relevant_ids)

        dcg = 0.0
        for rank, doc_id in enumerate(ids, start=1):
            if doc_id in relevant_set:
                dcg += 1.0 / math.log2(rank + 1)

        ideal_count = min(len(relevant_ids), k or len(relevant_ids))
        idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_count + 1))

        return dcg / idcg if idcg > 0 else 0.0

    @staticmethod
    def precision_at_k(
        retrieved_ids: list[str],
        relevant_ids: list[str],
        k: int,
    ) -> float:
        if k == 0:
            return 0.0
        top_k = retrieved_ids[:k]
        hits = len(set(top_k) & set(relevant_ids))
        return hits / k

    @staticmethod
    def recall_at_k(
        retrieved_ids: list[str],
        relevant_ids: list[str],
        k: int,
    ) -> float:
        if not relevant_ids:
            return 0.0
        top_k = retrieved_ids[:k]
        hits = len(set(top_k) & set(relevant_ids))
        return hits / len(relevant_ids)

    def evaluate(
        self,
        queries: list[str],
        all_retrieved_ids: list[list[str]],
        all_relevant_ids: list[list[str]],
        k_values: list[int] | None = None,
    ) -> dict:
        k_values = k_values or [5, 10, 20]
        results = {
            "hit_rate": [],
            "mrr": [],
        }
        for k in k_values:
            results[f"precision@{k}"] = []
            results[f"recall@{k}"] = []
            results[f"ndcg@{k}"] = []

        for retrieved, relevant in zip(all_retrieved_ids, all_relevant_ids):
            results["hit_rate"].append(self.hit_rate(retrieved, relevant))
            results["mrr"].append(self.mrr(retrieved, relevant))

            for k in k_values:
                results[f"precision@{k}"].append(
                    self.precision_at_k(retrieved, relevant, k)
                )
                results[f"recall@{k}"].append(
                    self.recall_at_k(retrieved, relevant, k)
                )
                results[f"ndcg@{k}"].append(
                    self.ndcg(retrieved, relevant, k=k)
                )

        averaged = {}
        for metric, values in results.items():
            averaged[metric] = sum(values) / len(values) if values else 0.0

        return averaged