from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Sequence

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


SentimentInfer = Callable[[Sequence[str], Sequence[str]], Any]

logger = logging.getLogger("waspada.rss_engine")


@dataclass(frozen=True)
class SentimentConfig:
    model_name: str
    labels: List[str]
    min_confidence: float
    batch_size: int
    contexts: List[str]
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

    def _normalize_output_label(self, label: str) -> str:
        normalized = label.strip().upper()
        if normalized in {"POSITIF", "NEGATIF"}:
            return normalized
        if self._config.labels:
            if label == self._config.labels[0]:
                return "POSITIF"
            if len(self._config.labels) > 1 and label == self._config.labels[1]:
                return "NEGATIF"
        return "NEGATIF"

    def _route_result(self, result: dict) -> str:
        label = result["labels"][0]
        return self._normalize_output_label(label)

    def _infer_with_model(self, texts: Sequence[str], labels: Sequence[str]) -> List[dict]:
        if not texts:
            return []

        contexts = [context.strip() for context in self._config.contexts if context.strip()]
        if not contexts:
            encodings = self._tokenizer(
                list(texts),
                truncation=True,
                padding=True,
                max_length=self._config.max_length,
                return_tensors="pt",
            ).to(self._device)
            with torch.no_grad():
                logits = self._model(**encodings).logits
                probs = torch.softmax(logits, dim=-1)
                best_scores, best_indices = torch.max(probs, dim=-1)
            return _format_predictions(best_indices, best_scores)

        paired_contexts: List[str] = []
        paired_texts: List[str] = []
        index_map: List[int] = []
        for text_index, text in enumerate(texts):
            for context in contexts:
                paired_contexts.append(context)
                paired_texts.append(text)
                index_map.append(text_index)

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

        best_scores = [-1.0 for _ in texts]
        best_indices = [0 for _ in texts]
        for pair_index, text_index in enumerate(index_map):
            pair_probs = probs[pair_index]
            score, label_index = torch.max(pair_probs, dim=-1)
            score_value = float(score.item())
            if score_value > best_scores[text_index]:
                best_scores[text_index] = score_value
                best_indices[text_index] = int(label_index.item())

        return _format_predictions(best_indices, best_scores)

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


def _format_predictions(indices: Sequence[int], scores: Sequence[float]) -> List[dict]:
    labels = ["NEGATIF", "POSITIF"]
    results: List[dict] = []
    for label_index, score in zip(indices, scores):
        label_index = int(label_index)
        label = labels[label_index] if label_index < len(labels) else labels[0]
        results.append({"labels": [label], "scores": [float(score)]})
    return results