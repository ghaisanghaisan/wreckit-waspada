from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from .config import AppConfig

logger = logging.getLogger("waspada.rss_engine.housekeeping")


async def delete_old_news_articles(pool, retention_days: int) -> int:
    if retention_days <= 0:
        logger.info("housekeeping.skip retention_days=%s", retention_days)
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM news_articles WHERE scraped_at < $1",
            cutoff,
        )
    if isinstance(result, str) and result.startswith("DELETE"):
        try:
            return int(result.split()[-1])
        except ValueError:
            return 0
    return 0


async def housekeeping_worker(config: AppConfig, pool) -> None:
    interval = int(config.housekeeping_interval_seconds)
    task = asyncio.current_task()
    task_name = getattr(task, "get_name", lambda: None)()
    logger.info(
        "housekeeping.start interval=%s retention_days=%s task=%s",
        interval,
        config.news_retention_days,
        task_name,
    )

    while True:
        logger.info("housekeeping.wake")
        try:
            deleted = await delete_old_news_articles(pool, config.news_retention_days)
            logger.info("housekeeping.deleted rows=%d retention_days=%s", deleted, config.news_retention_days)
        except Exception as exc:
            logger.exception("housekeeping.error %s", exc)

        if config.run_once:
            logger.info("housekeeping.exit_once")
            break

        await _sleep_with_jitter(interval)


async def _sleep_with_jitter(interval_seconds: int) -> None:
    await asyncio.sleep(interval_seconds + 0.25)
