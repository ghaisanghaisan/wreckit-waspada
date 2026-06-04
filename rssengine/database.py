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


async def fetch_agency_configs(pool: asyncpg.Pool) -> Sequence[TenantConfig]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT organization_id, keywords, sentiment_contexts
            FROM agency_configs
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

DELETE_OLD_ARTICLES_SQL = """
DELETE FROM news_articles
WHERE scraped_at < $1
"""

WEEKLY_REPORT_SQL = """
SELECT
    organization_id,
    count(*) AS article_count,
    sum((sentiment = 'POSITIF')::int) AS positive_count,
    sum((sentiment = 'NEGATIF')::int) AS negative_count,
    jsonb_object_agg(coalesce(source, 'unknown'), source_count) AS source_counts
FROM (
    SELECT organization_id, source, count(*) AS source_count
    FROM news_articles
    WHERE published_at >= $1 AND published_at < $2
    GROUP BY organization_id, source
) AS source_aggregates
GROUP BY organization_id
"""

UPSERT_WEEKLY_REPORT_SQL = """
INSERT INTO weekly_reports (
    id, organization_id, window_start, window_end, article_count, positive_count, negative_count, report, created_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9
)
ON CONFLICT (organization_id, window_start, window_end) DO UPDATE
SET article_count = EXCLUDED.article_count,
    positive_count = EXCLUDED.positive_count,
    negative_count = EXCLUDED.negative_count,
    report = EXCLUDED.report,
    created_at = EXCLUDED.created_at
"""

async def delete_old_news_articles(pool: asyncpg.Pool, retention_days: int) -> int:
    if retention_days <= 0:
        return 0

    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    async with pool.acquire() as conn:
        result = await conn.execute(DELETE_OLD_ARTICLES_SQL, cutoff)
    if isinstance(result, str) and result.startswith("DELETE"):
        try:
            return int(result.split()[-1])
        except ValueError:
            return 0
    return 0


async def fetch_weekly_article_metrics(pool: asyncpg.Pool, start_at, end_at) -> Sequence[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(WEEKLY_REPORT_SQL, start_at, end_at)
    return [
        {
            "organization_id": str(row["organization_id"]),
            "article_count": int(row["article_count"]),
            "positive_count": int(row["positive_count"]),
            "negative_count": int(row["negative_count"]),
            "source_counts": row["source_counts"] or {},
        }
        for row in rows
    ]


async def insert_weekly_reports(pool: asyncpg.Pool, rows: Iterable[Tuple]) -> None:
    if not rows:
        return
    prepared_rows = []
    for row in rows:
        row_list = list(row)
        if len(row_list) > 7 and isinstance(row_list[7], dict):
            row_list[7] = json.dumps(row_list[7])
        prepared_rows.append(tuple(row_list))
    async with pool.acquire() as conn:
        await conn.executemany(UPSERT_WEEKLY_REPORT_SQL, prepared_rows)
