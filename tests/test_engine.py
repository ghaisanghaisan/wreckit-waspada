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
async def test_ml_context_batching() -> None:
    def fake_infer(texts: Sequence[str], contexts: Sequence[str]):
        return [{context: {"label": "POSITIF", "score": 0.9} for context in contexts} for _ in texts]

    config = SentimentConfig(
        model_name="dummy",
        batch_size=3,
        max_length=256,
    )
    engine = SentimentEngine(config, asyncio.BoundedSemaphore(2), infer_fn=fake_infer)
    results = await engine.classify_contexts(["a", "b", "c"], ["ctx-1", "ctx-2"])
    assert results[0]["ctx-1"]["label"] == "POSITIF"


@pytest.mark.asyncio
async def test_semaphore_limits_concurrency() -> None:
    lock = threading.Lock()
    current = 0
    max_seen = 0

    def fake_infer(texts: Sequence[str], contexts: Sequence[str]):
        nonlocal current, max_seen
        with lock:
            current += 1
            max_seen = max(max_seen, current)
        time.sleep(0.05)
        with lock:
            current -= 1
        return [{"overall": {"label": "POSITIF", "score": 0.9}} for _ in texts]

    config = SentimentConfig(
        model_name="dummy",
        batch_size=1,
        max_length=256,
    )
    engine = SentimentEngine(config, asyncio.BoundedSemaphore(2), infer_fn=fake_infer)

    await asyncio.gather(*[engine.classify_contexts(["x"], ["overall"]) for _ in range(10)])
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

        async def fetch(self, query: str, organization_id: str, urls: Sequence[str]):
            return [{"url": "b"}]

    pool = FakePool()
    existing = await fetch_existing_urls(pool, "org-1", ["a", "b", "c"])
    assert existing == {"b"}