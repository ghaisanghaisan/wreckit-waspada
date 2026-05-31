from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Sequence, Set, Tuple

import asyncpg


UPSERT_SQL = """
INSERT INTO news_articles (
    id, organization_id, url, source, title, body, sentiment, processed_sentiment, published_at, scraped_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10
)
ON CONFLICT (organization_id, url) DO NOTHING
"""


@dataclass(frozen=True)
class TenantConfig:
    organization_id: str
    keywords: Sequence[str]
    sentiment_contexts: Sequence[str]


async def create_pool(dsn: str, min_size: int = 1, max_size: int = 10) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=dsn, min_size=min_size, max_size=max_size)


async def fetch_existing_urls(pool: asyncpg.Pool, organization_id: str, urls: Sequence[str]) -> Set[str]:
    if not urls:
        return set()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT url FROM news_articles WHERE organization_id = $1 AND url = ANY($2::text[])",
            organization_id,
            urls,
        )
    return {row["url"] for row in rows}


async def fetch_tenant_configs(pool: asyncpg.Pool) -> Sequence[TenantConfig]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT organization_id, keywords, sentiment_contexts
            FROM tenant_configs
            ORDER BY created_at ASC
            """
        )
    return [
        TenantConfig(
            organization_id=str(row["organization_id"]),
            keywords=row["keywords"] or [],
            sentiment_contexts=row["sentiment_contexts"] or [],
        )
        for row in rows
    ]


async def insert_rows(pool: asyncpg.Pool, rows: Iterable[Tuple]) -> None:
    if not rows:
        return
    prepared_rows = []
    for row in rows:
        row_list = list(row)
        if len(row_list) > 7 and isinstance(row_list[7], dict):
            row_list[7] = json.dumps(row_list[7])
        prepared_rows.append(tuple(row_list))
    async with pool.acquire() as conn:
        await conn.executemany(UPSERT_SQL, prepared_rows)