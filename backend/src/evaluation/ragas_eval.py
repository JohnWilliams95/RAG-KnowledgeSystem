from __future__ import annotations

import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel

from backend.src.generation.rag_chain import RAGChain

logger = logging.getLogger(__name__)


class RAGASEvaluator:
    def __init__(
        self,
        llm: BaseChatModel,
        embeddings=None,
    ):
        self._llm = llm
        self._embeddings = embeddings

    def evaluate(
        self,
        questions: list[str],
        answers: list[str],
        contexts: list[list[str]],
        ground_truths: Optional[list[str]] = None,
    ) -> dict:
        try:
            from ragas import evaluate
            from ragas.metrics import (
                context_recall,
                context_precision,
                faithfulness,
                answer_relevancy,
            )
            from ragas.dataset_schema import SingleTurnSample, EvaluationDataset

            samples = []
            for i, (q, a, ctx) in enumerate(zip(questions, answers, contexts)):
                sample = SingleTurnSample(
                    user_input=q,
                    response=a,
                    retrieved_contexts=ctx,
                )
                if ground_truths and i < len(ground_truths):
                    sample.reference = ground_truths[i]
                samples.append(sample)

            dataset = EvaluationDataset(samples=samples)

            metrics = [faithfulness, answer_relevancy]
            if ground_truths:
                metrics.extend([context_recall, context_precision])

            result = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self._llm,
                embeddings=self._embeddings,
            )

            return result.to_pandas().to_dict()

        except ImportError:
            logger.warning("ragas not installed. Install with: pip install ragas")
            return {"error": "ragas not installed"}
        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            return {"error": str(e)}