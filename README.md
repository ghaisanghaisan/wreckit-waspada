WASPADA adalah platform open-source pertama di Indonesia untuk pertahanan information warfare. Sistem ini melakukan monitoring terhadap media online Indonesia, mendeteksi narasi negatif yang terkoordinasi, menganalisis sentiment dengan AI berbahasa Indonesia, dan memberikan strategi mitigasi (debunking/prebunking) yang dihasilkan oleh LLM. Dirancang sebagai SaaS yang dapat diakses oleh kementerian, BUMN, partai politik, NGO, dan jurnalis investigasi.

**Tagline**: _Mata yang Tak Pernah Tidur_

**Problem statement**: Information warfare adalah ancaman nyata di Indonesia (pemilu disinformasi, hoax viral, foreign influence operations), namun tools enterprise seperti Meltwater dan Kazee sangat mahal dan tidak men-democratize akses. Lembaga non-pemerintah dan organisasi mid-size tertinggal dalam pertahanan informasi.

**Solusi**: Platform open-source yang memadukan media monitoring, sentiment analysis berbahasa Indonesia, deteksi koordinasi, dan AI-generated mitigation strategy dalam satu sistem terintegrasi.

# WASPADA: RSS Scraping and Research Pipeline

"WASPADA" is an asynchronous RSS ingestion engine. The system is split into small modules (config, scraper, ML engine, database, and orchestrator) to make development, testing, and production deployment easier.
This README now explains how the project works, how the pieces fit together, and how to get the engine running even if you are new to the codebase.

**Recommended Python version**: 3.12 or 3.13 (these are best-supported by PyTorch and Transformers). Python 3.14 may show deprecation warnings from PyTorch.

**What this project does (plain language)**

- Periodically fetches RSS/Atom feeds from configured sources.
- Parses the feed entries and extracts article metadata and a short body.
- Filters incoming items using simple keyword rules to avoid storing noise.
- Performs a batched, zero-shot sentiment classification (optional) using a HuggingFace model.
- Stores new articles into a PostgreSQL `news_articles` table, avoiding duplicates via dedup checks and upserts.

High-level flow (step-by-step)

1. The orchestrator (`rssengine/main.py`) schedules worker loops for each configured feed source.
2. A worker fetches the feed XML (`aiohttp`) and parses it (`feedparser` running in a thread to avoid blocking the event loop).
3. Parsed entries are normalized and run through `is_relevant()` keyword filters (cheap string matching).
4. Candidate URLs are deduplicated using an in-memory URL cache and a single DB query (`SELECT url FROM news_articles WHERE url = ANY(...)`) before any ML work is performed.
5. The remaining candidates are grouped into batches and sent to the `SentimentEngine` for zero-shot classification (run in `asyncio.to_thread` so inference is off the event loop) with concurrency limited by a `BoundedSemaphore`.
6. Finalized rows (metadata, body, labels, sentiment) are bulk inserted/upserted into Postgres using `asyncpg`.

Why this design? (short)

- Avoid waste: deduplicate before running heavy ML so CPU/memory isn't wasted on duplicates.
- Scale-friendly: batching + semaphore preserve memory and allow tuning to available resources.
- Async-first: network I/O (fetching feeds) is async for high throughput; heavy CPU work is run off-loop to avoid blocking.

Project layout (what to open first)

- `rssengine/config.py` — source list, global keywords, and environment defaults.
- `rssengine/scraper.py` — how feeds are fetched and how candidate articles are built.
- `rssengine/ml_engine.py` — model initialization, batching, and label routing.
- `rssengine/database.py` — `asyncpg` pool creation, dedup query, and bulk upsert SQL.
- `rssengine/main.py` — the orchestrator that wires everything together.

Quickstart (friendly, copy-paste)

1. Clone and enter the project

```zsh
git clone <repo-url>
cd wreckit-waspada
```

2. Create and activate a virtualenv (use Python 3.12/3.13)

```zsh
# example with python3.12
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

3. Install dependencies

```zsh
pip install -r requirements.txt
```

4. Start Postgres (recommended with docker-compose)

```zsh
docker-compose up -d
# wait until the DB reports healthy
```

5. (Optional) Initialize/reset DB

```zsh
chmod +x scripts/reset_db.sh
./scripts/reset_db.sh
```

6. Run the engine (single-run or continuous)

```zsh
# one-shot (good for testing):
RUN_ONCE=1 python -m rssengine

# continuous run:
python -m rssengine
```

Notes for first run

- The first time you run the engine it will download the zero-shot model and might take several minutes and tens of MBs (or more) of RAM. This is expected.
- If you don't want sentiment inference, set `SENTIMENT_BATCH_SIZE=0` or modify `load_config()` to disable the ML step.

Running tests

```zsh
source .venv/bin/activate
pytest -q
```

If tests fail because of imports, ensure your current directory is project root and `.venv` is activated. You can also run:

```zsh
export PYTHONPATH="$PWD"
pytest -q
```

Configuration details

- The app reads env vars and falls back to defaults in `rssengine/config.py`.
- Important env vars: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `RUN_ONCE`, `SENTIMENT_MODEL_NAME`, `SENTIMENT_BATCH_SIZE`, `SENTIMENT_MAX_CONCURRENCY`.

Troubleshooting quick list

- DB connection failures: confirm `docker-compose` started Postgres and `POSTGRES_*` envs match; use `psql` to test connectivity.
- Model OOM or high memory: lower `SENTIMENT_MAX_CONCURRENCY` and `SENTIMENT_BATCH_SIZE`, or move model to a separate service.
- Duplicate rows: ensure `database/init.sql` contains unique constraint on `url` and `news_articles.sentiment` column exists.

Next steps I can help with

- Add a small Dockerfile and pinned Python runtime for the service.
- Add a GitHub Actions workflow to run tests on PRs.
- Add a minimal Prometheus metrics endpoint to monitor throughput and latency.

If you want, I can now:

- run `pytest -q` and report results,
- add a `Dockerfile` for the Python service,
- or create a small `docker-compose` service for the Python worker.

Tell me which next step you prefer and I'll proceed.
