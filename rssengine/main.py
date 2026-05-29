from __future__ import annotations

import asyncio
import logging
import random
import uuid
from collections import deque
from typing import Iterable, List, Sequence

import aiohttp

from .config import AppConfig, RSSSourceConfig, load_config
from .database import create_pool, fetch_existing_urls, insert_rows
from .ml_engine import SentimentConfig, SentimentEngine
from .scraper import Candidate, collect_candidates, fetch_xml, parse_feed


logger = logging.getLogger("waspada.rss_engine")


class UrlCache:
    def __init__(self, maxlen: int) -> None:
        self._deque = deque(maxlen=maxlen)
        self._set: set[str] = set()
        self._lock = asyncio.Lock()

    async def filter_new(self, urls: Sequence[str]) -> List[str]:
        if not urls:
            return []
        async with self._lock:
            return [url for url in urls if url not in self._set]

    async def update(self, urls: Iterable[str]) -> None:
        async with self._lock:
            for url in urls:
                if url in self._set:
                    continue
                if len(self._deque) == self._deque.maxlen:
                    evicted = self._deque.popleft()
                    self._set.discard(evicted)
                self._deque.append(url)
                self._set.add(url)


def build_rows(source: str, candidates: Sequence[Candidate], sentiments: Sequence[str]) -> List[tuple]:
    from datetime import datetime, timezone

    scraped_at = datetime.now(timezone.utc)
    rows = []
    for candidate, sentiment in zip(candidates, sentiments):
        rows.append(
            (
                uuid.uuid4(),
                candidate.url,
                source,
                candidate.title,
                candidate.body,
                sentiment,
                candidate.published_at,
                scraped_at,
            )
        )
    return rows


async def worker(
    config: AppConfig,
    source_config: RSSSourceConfig,
    pool,
    session: aiohttp.ClientSession,
    sentiment_engine: SentimentEngine,
    url_cache: UrlCache,
) -> None:
    keywords = source_config.keywords or config.global_keywords
    interval = int(source_config.interval_seconds)
    task = asyncio.current_task()
    task_name = getattr(task, "get_name", lambda: None)()
    logger.info("worker.start source=%s url=%s task=%s", source_config.source, source_config.url, task_name)

    while True:
        logger.info("worker.wake source=%s url=%s", source_config.source, source_config.url)
        try:
            raw_xml = await fetch_xml(
                session,
                source_config.url,
                timeout_seconds=config.request_timeout_seconds,
                retries=config.fetch_retries,
                backoff_base=config.fetch_backoff_base,
                user_agent=config.user_agent,
                logger=logger,
            )
            feed = await parse_feed(raw_xml)
            fetched = len(feed.entries)

            # 1) Parse + cheap keyword filter (O(N) string checks).
            candidates = collect_candidates(feed, keywords)
            candidate_urls = [candidate.url for candidate in candidates]

            # 2) Cache filter to avoid frequent DB hits on hot loops.
            filtered_urls = await url_cache.filter_new(candidate_urls)
            filtered_set = set(filtered_urls)
            candidates = [candidate for candidate in candidates if candidate.url in filtered_set]
            if not candidates:
                logger.info("worker.empty source=%s fetched=%d passed=0", source_config.source, fetched)
                if config.run_once:
                    logger.info("worker.exit_once source=%s", source_config.source)
                    break
                await _sleep_with_jitter(interval)
                continue

            # 3) DB dedup BEFORE ML to avoid O(N) CPU waste on already-seen URLs.
            existing = await fetch_existing_urls(pool, [candidate.url for candidate in candidates])
            new_candidates = [candidate for candidate in candidates if candidate.url not in existing]
            if not new_candidates:
                logger.info("worker.empty source=%s fetched=%d passed=0", source_config.source, fetched)
                if config.run_once:
                    logger.info("worker.exit_once source=%s", source_config.source)
                    break
                await _sleep_with_jitter(interval)
                continue

            # 4) Batched ML inference (semaphore-limited) to minimize overhead.
            texts = [f"{candidate.title} {candidate.body}".strip() or " " for candidate in new_candidates]
            sentiments = await sentiment_engine.classify_batch(texts)
            rows = build_rows(source_config.source, new_candidates, sentiments)

            positives = sum(1 for sentiment in sentiments if sentiment == "POSITIF")
            negatives = sum(1 for sentiment in sentiments if sentiment == "NEGATIF")
            neutrals = len(sentiments) - positives - negatives
            logger.info(
                "sentiment.analyzed source=%s total=%d positif=%d negatif=%d netral=%d",
                source_config.source,
                len(sentiments),
                positives,
                negatives,
                neutrals,
            )

            await insert_rows(pool, rows)
            await url_cache.update([candidate.url for candidate in new_candidates])
            logger.info(
                "worker.inserted source=%s fetched=%d passed=%d inserted=%d",
                source_config.source,
                fetched,
                len(new_candidates),
                len(rows),
            )
        except Exception as exc:
            logger.exception("worker.error source=%s url=%s error=%s", source_config.source, source_config.url, exc)

        if config.run_once:
            logger.info("worker.exit_once source=%s", source_config.source)
            break

        await _sleep_with_jitter(interval)


async def _sleep_with_jitter(interval_seconds: int) -> None:
    await asyncio.sleep(interval_seconds + random.uniform(0, 1.0))


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config = load_config()

    logger.warning("woiii connection=%s", config.db_dsn)

    sentiment_config = SentimentConfig(
        model_name=config.model_name,
        labels=config.sentiment_labels,
        min_confidence=config.sentiment_min_confidence,
        batch_size=config.sentiment_batch_size,
        contexts=config.sentiment_contexts,
        max_length=config.sentiment_max_length,
    )

    semaphore = asyncio.BoundedSemaphore(config.sentiment_max_concurrency)
    sentiment_engine = SentimentEngine(sentiment_config, semaphore)
    url_cache = UrlCache(config.url_cache_maxlen)



    pool = await create_pool(config.db_dsn, min_size=1, max_size=10)
    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(worker(config, source, pool, session, sentiment_engine, url_cache), name=source.source)
            for source in config.sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error("worker task %s raised: %s", task.get_name(), result)

    await pool.close()

    # Phase 2: move inference to a queue/microservice (e.g., Celery/RabbitMQ) to isolate ML latency.


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("engine.shutdown")