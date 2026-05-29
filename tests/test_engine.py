from __future__ import annotations

import asyncio
import threading
import time
from typing import Sequence

import pytest

from rssengine.database import fetch_existing_urls
from rssengine.ml_engine import SentimentConfig, SentimentEngine
from rssengine.scraper import is_relevant, normalize_keywords


def test_is_relevant_case_insensitive() -> None:
    keywords = normalize_keywords(["polri", "MABES"])
    assert is_relevant("Kegiatan Polri", "", keywords) is True
    assert is_relevant("", "Mabes Polri membantah", keywords) is True
    assert is_relevant("Berita ekonomi", "Tidak terkait", keywords) is False


@pytest.mark.asyncio
async def test_ml_routing_with_confidence_threshold() -> None:
    def fake_infer(texts: Sequence[str], labels: Sequence[str]):
        return [
            {"labels": [labels[0], labels[1], labels[2]], "scores": [0.9, 0.05, 0.05]},
            {"labels": [labels[1], labels[0], labels[2]], "scores": [0.8, 0.1, 0.1]},
            {"labels": [labels[0], labels[1], labels[2]], "scores": [0.2, 0.1, 0.7]},
        ]

    config = SentimentConfig(
        model_name="dummy",
        labels=["POS", "NEG", "NEU"],
        min_confidence=0.4,
        batch_size=3,
        contexts=[],
        max_length=256,
    )
    engine = SentimentEngine(config, asyncio.BoundedSemaphore(2), infer_fn=fake_infer)
    results = await engine.classify_batch(["a", "b", "c"])
    assert results == ["POSITIF", "NEGATIF", "POSITIF"]


@pytest.mark.asyncio
async def test_semaphore_limits_concurrency() -> None:
    lock = threading.Lock()
    current = 0
    max_seen = 0

    def fake_infer(texts: Sequence[str], labels: Sequence[str]):
        nonlocal current, max_seen
        with lock:
            current += 1
            max_seen = max(max_seen, current)
        time.sleep(0.05)
        with lock:
            current -= 1
        return [{"labels": [labels[0]], "scores": [0.9]} for _ in texts]

    config = SentimentConfig(
        model_name="dummy",
        labels=["POS", "NEG", "NEU"],
        min_confidence=0.4,
        batch_size=1,
        contexts=[],
        max_length=256,
    )
    engine = SentimentEngine(config, asyncio.BoundedSemaphore(2), infer_fn=fake_infer)

    await asyncio.gather(*[engine.classify_batch(["x"]) for _ in range(10)])
    assert max_seen <= 2


@pytest.mark.asyncio
async def test_db_dedup_filters_existing_urls() -> None:
    class FakePool:
        def acquire(self):
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def fetch(self, query: str, urls: Sequence[str]):
            return [{"url": "b"}]

    pool = FakePool()
    existing = await fetch_existing_urls(pool, ["a", "b", "c"])
    assert existing == {"b"}