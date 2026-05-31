from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Sequence

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


SentimentInfer = Callable[[Sequence[str], Sequence[str]], Any]
LABELS = ["NEGATIF", "POSITIF"]

logger = logging.getLogger("waspada.rss_engine")


@dataclass(frozen=True)
class SentimentConfig:
    model_name: str
    batch_size: int
    max_length: int


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
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._tokenizer = AutoTokenizer.from_pretrained(config.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(config.model_name)
            self._model.to(self._device)
            self._model.eval()
            self._infer_fn = self._infer_with_model
        else:
            self._infer_fn = infer_fn

    def _infer_with_model(self, texts: Sequence[str], contexts: Sequence[str]) -> List[dict]:
        if not texts:
            return []

        normalized_contexts = [context.strip() for context in contexts if context.strip()]
        if not normalized_contexts:
            normalized_contexts = ["overall"]

        paired_contexts: List[str] = []
        paired_texts: List[str] = []
        index_map: List[int] = []
        context_map: List[str] = []
        for text_index, text in enumerate(texts):
            for context in normalized_contexts:
                paired_contexts.append(context)
                paired_texts.append(text)
                index_map.append(text_index)
                context_map.append(context)

        encodings = self._tokenizer(
            paired_contexts,
            paired_texts,
            truncation=True,
            padding=True,
            max_length=self._config.max_length,
            return_tensors="pt",
        ).to(self._device)
        with torch.no_grad():
            logits = self._model(**encodings).logits
            probs = torch.softmax(logits, dim=-1)

        results: List[dict] = [dict() for _ in texts]
        for pair_index, text_index in enumerate(index_map):
            score, label_index = torch.max(probs[pair_index], dim=-1)
            label = LABELS[int(label_index.item())] if label_index.item() < len(LABELS) else LABELS[0]
            results[text_index][context_map[pair_index]] = {
                "label": label,
                "score": float(score.item()),
            }

        return results

    async def classify_contexts(self, texts: Sequence[str], contexts: Sequence[str]) -> List[dict]:
        if not texts:
            return []
        outputs: List[dict] = []
        for batch in _chunk_list(list(texts), self._config.batch_size):
            async with self._semaphore:
                results = await asyncio.to_thread(self._infer_fn, batch, contexts)
            if isinstance(results, dict):
                results = [results]
            outputs.extend(results)
        return outputs


def _chunk_list(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def summarize_sentiment(context_sentiments: dict) -> str:
    if not context_sentiments:
        return "NEGATIF"
    positives = sum(1 for payload in context_sentiments.values() if payload.get("label") == "POSITIF")
    negatives = sum(1 for payload in context_sentiments.values() if payload.get("label") == "NEGATIF")
    return "POSITIF" if positives >= negatives else "NEGATIF"