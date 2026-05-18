# WASPADA: RSS Scraping and Research Pipeline

"WASPADA" is an asynchronous RSS ingestion engine. The system is split into small modules (config, scraper, ML engine, database, and orchestrator) to make development, testing, and production deployment easier.

This README explains how to set up, run, and test the project locally and in CI.

**Recommended Python version**: 3.12 or 3.13 (PyTorch / Transformers are best supported on these versions). Python 3.14 may produce deprecation warnings from PyTorch.

## Project Layout

- `database/` — SQL initialization scripts (e.g. `init.sql`).
- `rssengine/` — main python package:
  - `config.py` — environment and app configuration.
  - `scraper.py` — network fetch, feed parsing and keyword filter.
  - `ml_engine.py` — HuggingFace pipeline singleton + batched inference.
  - `database.py` — asyncpg pool, batch dedup query, and bulk insert.
  - `main.py` — orchestrator (entrypoint).
  - `rss_engine.py` — legacy single-file engine (kept for reference).
- `scripts/reset_db.sh` — convenience script to drop all tables and re-run `database/init.sql`.
- `tests/` — pytest suite (`tests/test_engine.py`).
- `requirements.txt` — Python dependencies.

## Quickstart (local, recommended)

1. Clone & enter project root

```bash
git clone <repo-url>
cd wreckit-waspada
```

2. Create and activate a virtual environment (use Python 3.12/3.13)

```bash
# example with python3.12 (install python3.12 first or use pyenv)
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

3. Install Python dependencies

```bash
pip install -r requirements.txt
```

4. Start PostgreSQL (recommended: docker-compose provided)

```bash
docker-compose up -d
# wait until Postgres is healthy
```

5. Initialize / Reset the DB (optional — destructive)

```bash
chmod +x scripts/reset_db.sh
./scripts/reset_db.sh
```

6. Run the engine

```bash
# run continuously
python -m rssengine

# or run just once (useful for testing)
RUN_ONCE=1 python -m rssengine
```

Notes:

- The first run will load the HuggingFace model and may take some time and memory.

## Running Tests

1. Make sure the venv is activated and dependencies are installed (see above).

2. Run pytest:

```bash
pytest -q
# or run specific tests
pytest -q tests/test_engine.py
```

The tests use lightweight mocks for the ML and DB layers and exercise keyword filtering, sentiment routing, and semaphore concurrency.

If pytest fails with import issues, ensure your current working directory is the project root and that `.venv` is activated. You can also set `PYTHONPATH`:

```bash
export PYTHONPATH="$PWD"
```

## Configuration & Environment

The app reads configuration from environment variables with sensible defaults. Key variables:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` — DB connection.
- `RUN_ONCE` — set to `1` for a single-run ingestion (helpful for local tests).
- `SENTIMENT_MODEL_NAME` — HF model name (default: `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`).
- `SENTIMENT_BATCH_SIZE`, `SENTIMENT_MAX_CONCURRENCY` — tune ML batching and concurrency.

You can set these inline when running, e.g.: `POSTGRES_PASSWORD=secret RUN_ONCE=1 python -m rssengine`.

## Production Notes & Troubleshooting

- PyTorch compatibility: PyTorch currently warns about `torch.jit.script` on Python 3.14. Use Python 3.12/3.13 for production to avoid deprecation warnings and runtime risk. The code suppresses the warning for development convenience but using a supported Python version is recommended.
- Model memory: The HF zero-shot model is large. The engine uses a `BoundedSemaphore` and batching to avoid concurrent large inferences; tune `SENTIMENT_MAX_CONCURRENCY` and `SENTIMENT_BATCH_SIZE` according to available RAM/GPU.
- Decoupling ML: For scale, move inference to a dedicated service (Phase 2) — e.g., an HTTP model server or a job queue (Celery/RabbitMQ) to isolate memory/latency.
- DB schema: `database/init.sql` contains the `news_articles` table definition. Ensure the `sentiment` VARCHAR column exists before running the engine.

## Development Tips

- Use `RUN_ONCE=1` to test single-run behavior quickly.
- Add or modify sources in `rssengine/config.py` via `load_config()` or by injecting a custom `AppConfig` when running programmatically.
- Read logs to inspect per-source metrics: fetched / passed filter / analyzed sentiment counts.
