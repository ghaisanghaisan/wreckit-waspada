# PostgreSQL (pgvector) container blueprint

This workspace contains a database container blueprint and example ingestion scripts for high-volume web scraping. It uses `pgvector/pgvector:pg16` and enables `uuid-ossp`, `vector` (pgvector), and `pg_trgm` extensions.

**Files added**

- `docker-compose.yml`: service for PostgreSQL 16 (pgvector image), mounts `db/init` for initialization SQL and forces `timezone='UTC'`.
- `db/init/init.sql`: creates extensions, tables `news_articles` and `social_posts`, and the necessary indexes (B-Tree and GIN).
- `scripts/psycopg2_upsert.py`: synchronous ingestion sample using `psycopg2` with `ON CONFLICT (url) DO UPDATE` for `news_articles`.
- `scripts/asyncpg_upsert.py`: async ingestion sample using `asyncpg` for `social_posts` showing JSONB array usage.
- `rss_engine.py`: async RSS ingestion engine (aiohttp + feedparser + asyncpg).
- `requirements.txt`: Python dependencies for the async RSS engine.

**How to run**

1. Start the DB container (from project root):

```bash
docker-compose up -d
```

2. Wait for the DB to be healthy, then run examples (adjust `DATABASE_URL` env var if needed):

```bash
export DATABASE_URL=postgresql://postgres:examplepassword@localhost:5432/waspada
python3 scripts/psycopg2_upsert.py
python3 scripts/asyncpg_upsert.py
```

3. Run the async RSS engine (after installing deps):

```bash
python3 -m pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:examplepassword@localhost:5432/waspada
python3 rss_engine.py
```

Optional one-shot run:

```bash
RUN_ONCE=1 python3 rss_engine.py
```

**Notes / Best practices**

- Timezone: All timestamp columns are `TIMESTAMPTZ`. In Python, always pass timezone-aware datetimes (`datetime.timezone.utc`). The container is configured to use UTC (`timezone='UTC'`).
- Upserts: Use `ON CONFLICT (url) DO UPDATE` for `news_articles` ingestion to avoid duplicate scrapes.
- JSONB operators: When filtering by engagement metrics, use `->>` and cast to integer, e.g.:

```sql
SELECT * FROM social_posts WHERE (engagement ->> 'likes')::int > 100;
```

- Array operators: When filtering by tags or media URLs use `= ANY()` or `&&`, e.g.:

```sql
SELECT * FROM news_articles WHERE 'politics' = ANY(tags);
SELECT * FROM social_posts WHERE media_urls && ARRAY['https://.../image.jpg'];
```

- Indexes: GIN indexes are used for `tags` (array) and `engagement` (JSONB). B-Tree indexes are used for common filtering columns.

If you want, I can:

- add a tiny test harness to validate the schema after container start,
- add a `Makefile` or `docker-compose` profile for production settings,
- or wire a small ingestion worker demonstrating batch upserts and backoff.
