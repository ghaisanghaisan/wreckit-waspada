from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Sequence

from transformers import pipeline


SentimentInfer = Callable[[Sequence[str], Sequence[str]], Any]

logger = logging.getLogger("waspada.rss_engine")


@dataclass(frozen=True)
class SentimentConfig:
    model_name: str
    labels: List[str]
    min_confidence: float
    batch_size: int


class SentimentEngine:
    def __init__(
        self,
        config: SentimentConfig,
        semaphore: asyncio.BoundedSemaphore,
        infer_fn: SentimentInfer | None = None,
    ) -> None:
        self._config = config
        self._semaphore = semaphore
        if infer_fn is None:
            logger.info("sentiment.load model=%s", config.model_name)
            hf_pipeline = pipeline(
                "zero-shot-classification",
                model=config.model_name,
            )
            self._infer_fn: SentimentInfer = lambda texts, labels: hf_pipeline(texts, labels)
        else:
            self._infer_fn = infer_fn

    def _map_label(self, label: str) -> str:
        if label == self._config.labels[0]:
            return "POSITIF"
        else:
            return "NEGATIF"

    def _route_result(self, result: dict) -> str:
        label = result["labels"][0]
        score = float(result["scores"][0])
        # if score < self._config.min_confidence:
        #     return "NETRAL"
        return self._map_label(label)

    async def classify_batch(self, texts: Sequence[str]) -> List[str]:
        if not texts:
            return []
        sentiments: List[str] = []
        for batch in _chunk_list(list(texts), self._config.batch_size):
            async with self._semaphore:
                results = await asyncio.to_thread(self._infer_fn, batch, self._config.labels)
            if isinstance(results, dict):
                results = [results]
            sentiments.extend(self._route_result(result) for result in results)
        return sentiments


def _chunk_list(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]