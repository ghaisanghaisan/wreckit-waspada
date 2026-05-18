from __future__ import annotations

from typing import Iterable, Sequence, Set, Tuple

import asyncpg


UPSERT_SQL = """
INSERT INTO news_articles (
    id, url, source, title, body, sentiment, published_at, scraped_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8
)
ON CONFLICT (url) DO NOTHING
"""


async def create_pool(dsn: str, min_size: int = 1, max_size: int = 10) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=dsn, min_size=min_size, max_size=max_size)


async def fetch_existing_urls(pool: asyncpg.Pool, urls: Sequence[str]) -> Set[str]:
    if not urls:
        return set()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT url FROM news_articles WHERE url = ANY($1::text[])",
            urls,
        )
    return {row["url"] for row in rows}


async def insert_rows(pool: asyncpg.Pool, rows: Iterable[Tuple]) -> None:
    if not rows:
        return
    async with pool.acquire() as conn:
        await conn.executemany(UPSERT_SQL, rows)