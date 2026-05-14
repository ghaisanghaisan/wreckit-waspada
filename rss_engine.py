import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

import aiohttp
import asyncpg
import feedparser

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:examplepassword@localhost:5432/waspada",
)

CONFIGS = [
    {"source": "detik.com", "url": "https://news.detik.com/berita/rss", "interval_seconds": 10},
]

RUN_ONCE = os.getenv("RUN_ONCE", "0") == "1"
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
FETCH_RETRIES = int(os.getenv("FETCH_RETRIES", "3"))
FETCH_BACKOFF_BASE = float(os.getenv("FETCH_BACKOFF_BASE", "1.5"))
USER_AGENT = os.getenv("USER_AGENT", "waspada-rss-bot/1.0")

logger = logging.getLogger("waspada.rss_engine")

UPSERT_SQL = """
INSERT INTO news_articles (
    id, url, source, title, body, published_at, scraped_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7
)
ON CONFLICT (url) DO NOTHING
"""


def to_utc_datetime(parsed_time):
    if not parsed_time:
        return None
    return datetime(
        parsed_time.tm_year,
        parsed_time.tm_mon,
        parsed_time.tm_mday,
        parsed_time.tm_hour,
        parsed_time.tm_min,
        parsed_time.tm_sec,
        tzinfo=timezone.utc,
    )


def extract_body(entry) -> str:
    if "content" in entry and entry.content:
        value = getattr(entry.content[0], "value", None)
        if value:
            return value
    summary = getattr(entry, "summary", None)
    return summary or ""


def build_rows(source: str, feed) -> list[tuple]:
    now = datetime.now(timezone.utc)
    rows = []
    for entry in feed.entries:
        url = getattr(entry, "link", None)
        if not url:
            continue

        title = getattr(entry, "title", "") or ""
        body = extract_body(entry)

        published_at = (
            to_utc_datetime(getattr(entry, "published_parsed", None))
            or to_utc_datetime(getattr(entry, "updated_parsed", None))
            or now
        )

        rows.append(
            (
                uuid.uuid4(),
                url,
                source,
                title,
                body,
                published_at,
                now,
            )
        )
    return rows


async def fetch_xml(session: aiohttp.ClientSession, url: str) -> str:
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
    headers = {"User-Agent": USER_AGENT}
    last_exc = None

    for attempt in range(1, FETCH_RETRIES + 1):
        try:
            async with session.get(url, timeout=timeout, headers=headers) as response:
                response.raise_for_status()
                return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            backoff = FETCH_BACKOFF_BASE ** (attempt - 1)
            logger.warning(
                "fetch.retry url=%s attempt=%d/%d error=%s backoff=%.2fs",
                url,
                attempt,
                FETCH_RETRIES,
                type(exc).__name__,
                backoff,
            )
            if attempt < FETCH_RETRIES:
                await asyncio.sleep(backoff)

    logger.exception("fetch.failed url=%s attempts=%d", url, FETCH_RETRIES)
    raise last_exc


async def parse_feed(raw_xml: str):
    return await asyncio.to_thread(feedparser.parse, raw_xml)


async def ingest_loop(pool: asyncpg.Pool, session: aiohttp.ClientSession, config: dict):
    source = config["source"]
    url = config["url"]
    interval = int(config["interval_seconds"])

    while True:
        logger.info("worker.wake source=%s url=%s", source, url)
        try:
            raw_xml = await fetch_xml(session, url)
            feed = await parse_feed(raw_xml)
            rows = build_rows(source, feed)

            if rows:
                async with pool.acquire() as conn:
                    await conn.executemany(UPSERT_SQL, rows)
                logger.info("worker.inserted source=%s rows=%d", source, len(rows))
            else:
                logger.info("worker.empty source=%s", source)
        except Exception as exc:
            logger.exception("worker.error source=%s url=%s error=%s", source, url, exc)

        if RUN_ONCE:
            logger.info("worker.exit_once source=%s", source)
            break

        logger.info("worker.sleep source=%s seconds=%d", source, interval)
        await asyncio.sleep(interval)


async def ingest_loop_debug(session: aiohttp.ClientSession, config: dict):
    source = config["source"]
    url = config["url"]
    interval = int(config["interval_seconds"])

    while True:
        logger.info("worker.wake source=%s url=%s", source, url)
        try:
            raw_xml = await fetch_xml(session, url)
            feed = await parse_feed(raw_xml)
            rows = build_rows(source, feed)

            if rows:
                # async with pool.acquire() as conn:
                #     await conn.executemany(UPSERT_SQL, rows)
                logger.info("worker.inserted source=%s rows=%d", source, len(rows))
                logger.info("debug.printrow \n\tsource=%s\n\ttitle=%s\n\tbody=%s", rows[0][2], rows[0][3], rows[0][4])
            else:
                logger.info("worker.empty source=%s", source)
        except Exception as exc:
            logger.exception("worker.error source=%s url=%s error=%s", source, url, exc)

        if RUN_ONCE:
            logger.info("worker.exit_once source=%s", source)
            break

        logger.info("worker.sleep source=%s seconds=%d", source, interval)
        await asyncio.sleep(interval)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger.info("engine.start configs=%d", len(CONFIGS))

    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(ingest_loop_debug(session, config)) for config in CONFIGS]
        await asyncio.gather(*tasks)

    # pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10)
    # async with aiohttp.ClientSession() as session:
    #     tasks = [asyncio.create_task(ingest_loop(pool, session, config)) for config in CONFIGS]
    #     await asyncio.gather(*tasks)
    # await pool.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("engine.shutdown")
