# WASPADA: RSS Scraping and Research Pipeline

This project is a high-performance RSS scraping engine designed to collect and store news articles and social media posts for further analysis. The scraped data is stored in a PostgreSQL database and will be fed into an LLM (Large Language Model) for advanced research and insights (WIP).

## Features

- **RSS Scraping Engine**: Asynchronous scraping of RSS feeds using `aiohttp`, `feedparser`, and `asyncpg`.
- **Database**: PostgreSQL 16 with extensions for semantic search (`pgvector`), UUID generation (`uuid-ossp`), and text search (`pg_trgm`).
- **Data Models**:
  - `news_articles`: Stores articles with metadata like `source`, `title`, `body`, `tags`, and timestamps.
  - `social_posts`: Stores social media posts with engagement metrics and media URLs.
- **Future Integration**: Data pipeline to feed scraped content into an LLM for research and analysis (WIP).

## Files

- `docker-compose.yml`: Service for PostgreSQL 16 (pgvector image), mounts `database/init.sql` for initialization SQL and forces `timezone='UTC'`.
- `database/init.sql`: Creates extensions, tables `news_articles` and `social_posts`, and the necessary indexes (B-Tree and GIN).
- `rssengine/psycopg2_upsert.py`: Synchronous ingestion sample using `psycopg2` with `ON CONFLICT (url) DO UPDATE` for `news_articles`.
- `rssengine/asyncpg_upsert.py`: Async ingestion sample using `asyncpg` for `social_posts` showing JSONB array usage.
- `rssengine/rss_engine.py`: Async RSS ingestion engine (aiohttp + feedparser + asyncpg).
- `requirements.txt`: Python dependencies for the async RSS engine.

## How to Run

1. **Start the Database**:

```bash
docker-compose up -d
```

2. **Wait for the Database to be Healthy**:

Ensure the database is ready before running scripts.

3. **Run Example Scripts**:

```bash
export DATABASE_URL=postgresql://postgres:examplepassword@localhost:5432/waspada
python3 rssengine/psycopg2_upsert.py
python3 rssengine/asyncpg_upsert.py
```

4. **Run the RSS Engine**:

Install dependencies and start the engine:

```bash
python3 -m pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:examplepassword@localhost:5432/waspada
python3 rssengine/rss_engine.py
```

Optional one-shot run:

```bash
RUN_ONCE=1 python3 rssengine/rss_engine.py
```

## Notes / Best Practices

- **Timezone**: All timestamp columns are `TIMESTAMPTZ`. In Python, always pass timezone-aware datetimes (`datetime.timezone.utc`). The container is configured to use UTC (`timezone='UTC'`).
- **Upserts**: Use `ON CONFLICT (url) DO UPDATE` for `news_articles` ingestion to avoid duplicate scrapes.
- **JSONB Operators**: When filtering by engagement metrics, use `->>` and cast to integer, e.g.:

```sql
SELECT * FROM social_posts WHERE (engagement ->> 'likes')::int > 100;
```

- **Array Operators**: When filtering by tags or media URLs use `= ANY()` or `&&`, e.g.:

```sql
SELECT * FROM news_articles WHERE 'politics' = ANY(tags);
SELECT * FROM social_posts WHERE media_urls && ARRAY['https://.../image.jpg'];
```

- **Indexes**: GIN indexes are used for `tags` (array) and `engagement` (JSONB). B-Tree indexes are used for common filtering columns.

## Future Work

- **LLM Integration**: Develop a pipeline to feed scraped data into an LLM for advanced research and insights.
- **Schema Validation**: Add a test harness to validate the database schema after container start.
- **Production Settings**: Add a `Makefile` or `docker-compose` profile for production deployments.
- **Batch Processing**: Implement a worker for batch upserts with retry/backoff logic.
