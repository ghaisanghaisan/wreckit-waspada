#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
import os
from dataclasses import dataclass
from typing import Iterable, List

import asyncpg


@dataclass(frozen=True)
class RegistrationPayload:
    name: str
    keywords: List[str]
    sentiment_contexts: List[str]


def parse_list(raw_values: Iterable[str]) -> List[str]:
    values: List[str] = []
    for raw in raw_values:
        if not raw:
            continue
        values.extend(item.strip() for item in raw.split(",") if item.strip())
    return values


def build_dsn() -> str:
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_pass = os.getenv("POSTGRES_PASSWORD", "gulingkanan")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "waspada")
    return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


async def register_organization(pool: asyncpg.Pool, payload: RegistrationPayload) -> str:
    async with pool.acquire() as conn:
        organization_id = await conn.fetchval(
            """
            INSERT INTO organizations (name)
            VALUES ($1)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            payload.name,
        )

        updated = await conn.execute(
            """
            UPDATE tenant_configs
            SET keywords = $2::text[],
                sentiment_contexts = $3::text[],
                updated_at = now()
            WHERE organization_id = $1
            """,
            organization_id,
            payload.keywords,
            payload.sentiment_contexts,
        )

        if updated == "UPDATE 0":
            await conn.execute(
                """
                INSERT INTO tenant_configs (organization_id, keywords, sentiment_contexts)
                VALUES ($1, $2::text[], $3::text[])
                """,
                organization_id,
                payload.keywords,
                payload.sentiment_contexts,
            )

    return str(organization_id)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register or update a tenant organization configuration.",
    )
    parser.add_argument("--name", required=True, help="Organization name")
    parser.add_argument(
        "--keywords",
        action="append",
        default=[],
        help="Comma-separated keywords list (repeatable)",
    )
    parser.add_argument(
        "--contexts",
        action="append",
        default=[],
        help="Comma-separated sentiment contexts list (repeatable)",
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("DATABASE_URL", ""),
        help="PostgreSQL DSN override (optional)",
    )

    args = parser.parse_args()
    keywords = parse_list(args.keywords)
    contexts = parse_list(args.contexts)

    if not keywords:
        raise SystemExit("At least one keyword is required. Use --keywords.")
    if not contexts:
        raise SystemExit("At least one sentiment context is required. Use --contexts.")

    payload = RegistrationPayload(
        name=args.name.strip(),
        keywords=keywords,
        sentiment_contexts=contexts,
    )

    dsn = args.dsn or build_dsn()
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=2)
    try:
        organization_id = await register_organization(pool, payload)
    finally:
        await pool.close()

    print(f"Registered organization '{payload.name}' with id {organization_id}.")


if __name__ == "__main__":
    asyncio.run(main())
