from __future__ import annotations

import logging
import os

import transformers

# Set standard Python logging to DEBUG globally
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


# Explicitly enable tqdm progress bars for downloads
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"

import asyncio
import random
import uuid
from collections import deque
from typing import Iterable, List, Sequence, Tuple

import aiohttp

from .config import AppConfig, RSSSourceConfig, load_config
from .database import TenantConfig, create_pool, fetch_existing_urls, fetch_agency_configs, insert_rows
from .ml_engine import SentimentConfig, SentimentEngine, summarize_sentiment
from .scraper import Candidate, collect_candidates, fetch_xml, is_relevant, normalize_keywords, parse_feed


logger = logging.getLogger("waspada.rss_engine")


class UrlCache:
    def __init__(self, maxlen: int) -> None:
        self._deque = deque(maxlen=maxlen)
        self._set: set[Tuple[str, str]] = set()
        self._lock = asyncio.Lock()

    async def filter_new(self, keys: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
        if not keys:
            return []
        async with self._lock:
            return [key for key in keys if key not in self._set]

    async def update(self, keys: Iterable[Tuple[str, str]]) -> None:
        async with self._lock:
            for key in keys:
                if key in self._set:
                    continue
                if len(self._deque) == self._deque.maxlen:
                    evicted = self._deque.popleft()
                    self._set.discard(evicted)
                self._deque.append(key)
                self._set.add(key)


def build_rows(
    source: str,
    organization_id: str,
    candidates: Sequence[Candidate],
    sentiments: Sequence[dict],
) -> List[tuple]:
    from datetime import datetime, timezone

    scraped_at = datetime.now(timezone.utc)
    rows = []
    for candidate, sentiment in zip(candidates, sentiments):
        rows.append(
            (
                uuid.uuid4(),
                organization_id,
                candidate.url,
                source,
                candidate.title,
                candidate.body,
                summarize_sentiment(sentiment),
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

            tenants = await fetch_agency_configs(pool)
            if not tenants:
                logger.info("worker.empty source=%s fetched=%d tenants=0", source_config.source, fetched)
                if config.run_once:
                    break
                await _sleep_with_jitter(interval)
                continue

            candidates = collect_candidates(feed, [])
            if not candidates:
                logger.info("worker.empty source=%s fetched=%d passed=0", source_config.source, fetched)
                if config.run_once:
                    break
                await _sleep_with_jitter(interval)
                continue

            for tenant in tenants:
                await _process_tenant_candidates(
                    pool=pool,
                    source=source_config.source,
                    tenant=tenant,
                    candidates=candidates,
                    sentiment_engine=sentiment_engine,
                    url_cache=url_cache,
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

    logger.info("LOADING SENTIMENT MODEL")

    sentiment_config = SentimentConfig(
        model_name=config.model_name,
        batch_size=config.sentiment_batch_size,
        max_length=config.sentiment_max_length,
    )

    semaphore = asyncio.BoundedSemaphore(config.sentiment_max_concurrency)
    sentiment_engine = SentimentEngine(sentiment_config, semaphore)
    url_cache = UrlCache(config.url_cache_maxlen)


    logger.info("CREATING POOL")

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



async def _process_tenant_candidates(
    pool,
    source: str,
    tenant: TenantConfig,
    candidates: Sequence[Candidate],
    sentiment_engine: SentimentEngine,
    url_cache: UrlCache,
) -> None:
    normalized_keywords = normalize_keywords(list(tenant.keywords))
    tenant_candidates = [
        candidate
        for candidate in candidates
        if is_relevant(candidate.title, candidate.body, normalized_keywords)
    ]
    if not tenant_candidates:
        return

    cache_keys = [(tenant.organization_id, candidate.url) for candidate in tenant_candidates]
    filtered_keys = await url_cache.filter_new(cache_keys)
    filtered_set = set(filtered_keys)
    tenant_candidates = [
        candidate
        for candidate in tenant_candidates
        if (tenant.organization_id, candidate.url) in filtered_set
    ]
    if not tenant_candidates:
        return

    existing = await fetch_existing_urls(
        pool,
        tenant.organization_id,
        [candidate.url for candidate in tenant_candidates],
    )
    new_candidates = [candidate for candidate in tenant_candidates if candidate.url not in existing]
    if not new_candidates:
        return

    texts = [f"{candidate.title} {candidate.body}".strip() or " " for candidate in new_candidates]
    sentiments = await sentiment_engine.classify_contexts(texts, tenant.sentiment_contexts)
    rows = build_rows(source, tenant.organization_id, new_candidates, sentiments)

    await insert_rows(pool, rows)
    await url_cache.update([(tenant.organization_id, candidate.url) for candidate in new_candidates])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("engine.shutdown")