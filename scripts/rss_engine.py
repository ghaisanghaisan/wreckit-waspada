import asyncio
import logging
import os
import uuid
from collections import deque
from datetime import datetime, timezone

import aiohttp
import asyncpg
import feedparser
from transformers import pipeline

DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'gulingkanan')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'waspada')

DB_DSN = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(DB_DSN)

GLOBAL_KEYWORDS = [
    # Nama Instansi & Singkatan
    "Polri", 
    "Polisi", 
    "Mabes Polri", 
    "Kepolisian Negara Republik Indonesia", 
    "Korps Bhayangkara",
    
    # Hierarki Wilayah (Polda & Polres)
    "Polda",        # Kepolisian Daerah
    "Polres",       # Kepolisian Resor
    "Polresta",     # Kepolisian Resor Kota
    "Polsek",       # Kepolisian Sektor
    
    # Jabatan & Pejabat Utama
    "Kapolri", 
    "Wakapolri", 
    "Kapolda", 
    "Kapolres", 
    "Kapolsek", 
    "Kadiv Humas Polri",
    
    # Korps & Divisi Spesifik
    "Bareskrim",    # Badan Reserse Kriminal
    "Korlantas",    # Korps Lalu Lintas
    "Brimob",       # Korps Brigade Mobil
    "Densus 88",    # Detasemen Khusus 88 Antiteror
    "Propam",       # Profesi dan Pengamanan
    "Ditlantas",    # Direktorat Lalu Lintas
    "Ditreskrimsus",# Direktorat Reserse Kriminal Khusus
    "Ditreskrimum", # Direktorat Reserse Kriminal Umum
    "Polda Metro Jaya", # Polda yang paling sering masuk berita nasional
    
    # Isu Operasional & Tugas Polisi
    "Kamtibmas",    # Keamanan dan ketertiban masyarakat
    "Operasi Ketupat", 
    "Operasi Lilin", 
    "Operasi Zebra", 
    "Tilang elektronik", 
    "ETLE",
    "Samsat",
    "SIM Keliling"
]

CONFIGS = [
    {
        "source": "antaranews.com",
        "url": "https://www.antaranews.com/rss/top-news",
        "interval_seconds": 10,
    },
    {
        "source": "liputan6.com",
        "url": "https://feed.liputan6.com/rss/news",
        "interval_seconds": 10,
    },
    {
        "source": "cnnindonesia.com",
        "url": "https://www.cnnindonesia.com/nasional/rss",
        "interval_seconds": 10,
    },
    {
        "source": "cnbcindonesia.com",
        "url": "https://www.cnbcindonesia.com/news/rss",
        "interval_seconds": 10,
    },
]

RUN_ONCE = os.getenv("RUN_ONCE", "0") == "1"
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
FETCH_RETRIES = int(os.getenv("FETCH_RETRIES", "3"))
FETCH_BACKOFF_BASE = float(os.getenv("FETCH_BACKOFF_BASE", "1.5"))
USER_AGENT = os.getenv("USER_AGENT", "waspada-rss-bot/1.0")
SENTIMENT_MAX_CONCURRENCY = int(os.getenv("SENTIMENT_MAX_CONCURRENCY", "2"))
SENTIMENT_BATCH_SIZE = int(os.getenv("SENTIMENT_BATCH_SIZE", "16"))

logger = logging.getLogger("waspada.rss_engine")

SENTIMENT_PIPELINE = None
SENTIMENT_POSITIVE = "apresiasi masyarakat, dukungan publik, kepuasan warga, pujian, kepercayaan publik, respons positif, pelayanan memuaskan, citra baik, pro-rakyat, antusiasme, kebanggaan, simpati masyarakat, sambutan hangat, harapan baru, kinerja gemilang, inovasi bermanfaat, keberpihakan pada rakyat, solusi tepat sasaran, dukungan netizen"
SENTIMENT_NEGATIVE = "kekecewaan publik, kritik tajam, penolakan warga, protes masyarakat, kecaman, krisis kepercayaan, kinerja buruk, ketidakpuasan, tuntutan, desakan mundur, viral negatif, kemarahan netizen, keresahan warga, polemik berkepanjangan, kontroversi, rapor merah, skeptisisme, dugaan penyelewengan, kecurigaan publik, reaksi keras, blunder"
SENTIMENT_NEUTRAL = "pengumuman resmi, sosialisasi kebijakan, agenda kegiatan, informasi faktual, laporan rutin, pernyataan prosedural, data statistik, regulasi pemerintah, kunjungan kerja, peresmian fasilitas, pelantikan pejabat, tata kelola birokrasi, seremonial, jadwal pelaksanaan, rilis pers, liputan langsung"

SENTIMENT_LABELS = [SENTIMENT_POSITIVE, SENTIMENT_NEGATIVE, SENTIMENT_NEUTRAL]
SENTIMENT_SEMAPHORE = asyncio.BoundedSemaphore(SENTIMENT_MAX_CONCURRENCY)

URL_CACHE_MAXLEN = int(os.getenv("URL_CACHE_MAXLEN", "500"))
URL_CACHE = deque(maxlen=URL_CACHE_MAXLEN)
URL_CACHE_SET = set()
URL_CACHE_LOCK = asyncio.Lock()

UPSERT_SQL = """
INSERT INTO news_articles (
    id, url, source, title, body, sentiment, published_at, scraped_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8
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


def normalize_keywords(keywords: list[str]) -> list[str]:
    return [keyword.strip().lower() for keyword in keywords if keyword and keyword.strip()]


def is_relevant(title: str, body: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    haystack = f"{title} {body}".lower()
    for keyword in keywords:
        if keyword in haystack:
            return True
    return False


def load_sentiment_pipeline():
    global SENTIMENT_PIPELINE
    if SENTIMENT_PIPELINE is None:
        logger.info("sentiment.load model=MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        SENTIMENT_PIPELINE = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        )


def classify_sentiment(text: str) -> str:
    if not SENTIMENT_PIPELINE:
        raise RuntimeError("Sentiment pipeline is not initialized")
    result = SENTIMENT_PIPELINE(text, SENTIMENT_LABELS)
    label = result["labels"][0]
    score = result["scores"][0]
    
    # Jika hasil sentiment ragu ragu e.g rata Positif, Negatif dan juga Netral
    # if score < 0.40:
    #     return "NETRAL"

    if label == SENTIMENT_POSITIVE:
        return "POSITIF"
    elif label == SENTIMENT_NEGATIVE:
        return "NEGATIF"
    else:
        return "NETRAL"


def map_sentiment_label(label: str) -> str:
    if label == SENTIMENT_POSITIVE:
        return "POSITIF"
    if label == SENTIMENT_NEGATIVE:
        return "NEGATIF"
    return "NETRAL"


def chunk_list(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


async def classify_sentiment_batch(texts: list[str]) -> list[str]:
    if not texts:
        return []
    async with SENTIMENT_SEMAPHORE:
        results = await asyncio.to_thread(SENTIMENT_PIPELINE, texts, SENTIMENT_LABELS)
    if isinstance(results, dict):
        results = [results]
    return [map_sentiment_label(result["labels"][0]) for result in results]


async def filter_cached_urls(urls: list[str]) -> list[str]:
    if not urls:
        return []
    async with URL_CACHE_LOCK:
        return [url for url in urls if url not in URL_CACHE_SET]


async def update_url_cache(urls: list[str]) -> None:
    if not urls:
        return
    async with URL_CACHE_LOCK:
        for url in urls:
            if url in URL_CACHE_SET:
                continue
            if len(URL_CACHE) == URL_CACHE_MAXLEN:
                evicted = URL_CACHE.popleft()
                URL_CACHE_SET.discard(evicted)
            URL_CACHE.append(url)
            URL_CACHE_SET.add(url)


async def fetch_existing_urls(conn: asyncpg.Connection, urls: list[str]) -> set[str]:
    if not urls:
        return set()
    rows = await conn.fetch("SELECT url FROM news_articles WHERE url = ANY($1::text[])", urls)
    return {row["url"] for row in rows}


def collect_candidates(feed, keywords: list[str]) -> list[dict]:
    now = datetime.now(timezone.utc)
    normalized_keywords = normalize_keywords(keywords)
    candidates = []
    for entry in feed.entries:
        url = getattr(entry, "link", None)
        if not url:
            continue
        title = getattr(entry, "title", "") or ""
        body = extract_body(entry)
        if not is_relevant(title, body, normalized_keywords):
            continue
        published_at = (
            to_utc_datetime(getattr(entry, "published_parsed", None))
            or to_utc_datetime(getattr(entry, "updated_parsed", None))
            or now
        )
        candidates.append(
            {
                "url": url,
                "title": title,
                "body": body,
                "published_at": published_at,
            }
        )
    return candidates


async def build_rows(source: str, candidates: list[dict]) -> list[tuple]:
    if not candidates:
        return []
    texts = [f"{item['title']} {item['body']}".strip() or " " for item in candidates]
    batches = chunk_list(texts, SENTIMENT_BATCH_SIZE)
    sentiments: list[str] = []
    for batch in batches:
        sentiments.extend(await classify_sentiment_batch(batch))
    now = datetime.now(timezone.utc)
    rows = []
    for item, sentiment in zip(candidates, sentiments):
        rows.append(
            (
                uuid.uuid4(),
                item["url"],
                source,
                item["title"],
                item["body"],
                sentiment,
                item["published_at"],
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
    keywords = config.get("keywords", GLOBAL_KEYWORDS)

    while True:
        logger.info("worker.wake source=%s url=%s", source, url)
        try:
            raw_xml = await fetch_xml(session, url)
            feed = await parse_feed(raw_xml)
            fetched = len(feed.entries)

            # 1) Parse + cheap keyword filter (O(N) string checks).
            candidates = collect_candidates(feed, keywords)
            candidate_urls = [item["url"] for item in candidates]

            # 2) Skip recent URLs in memory to avoid frequent DB hits.
            candidate_urls = await filter_cached_urls(candidate_urls)
            candidates = [item for item in candidates if item["url"] in candidate_urls]

            # 3) DB dedup BEFORE ML to avoid O(N) CPU waste on already-seen URLs.
            async with pool.acquire() as conn:
                existing = await fetch_existing_urls(conn, candidate_urls)
            new_candidates = [item for item in candidates if item["url"] not in existing]

            if not new_candidates:
                logger.info(
                    "worker.empty source=%s fetched=%d passed=0",
                    source,
                    fetched,
                )
                continue

            # 4) Batched ML inference (semaphore-limited) to minimize overhead.
            rows = await build_rows(source, new_candidates)

            if rows:
                positives = sum(1 for row in rows if row[5] == "POSITIF")
                negatives = sum(1 for row in rows if row[5] == "NEGATIF")
                neutrals = len(rows) - positives - negatives
                logger.info(
                    "sentiment.analyzed source=%s total=%d positif=%d negatif=%d netral=%d",
                    source,
                    len(rows),
                    positives,
                    negatives,
                    neutrals,
                )

            async with pool.acquire() as conn:
                await conn.executemany(UPSERT_SQL, rows)

            await update_url_cache([item["url"] for item in new_candidates])

            logger.info(
                "worker.inserted source=%s fetched=%d passed=%d inserted=%d",
                source,
                fetched,
                len(new_candidates),
                len(rows),
            )
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
    keywords = config.get("keywords", GLOBAL_KEYWORDS)

    while True:
        logger.info("worker.wake source=%s url=%s", source, url)
        try:
            raw_xml = await fetch_xml(session, url)
            feed = await parse_feed(raw_xml)
            candidates = collect_candidates(feed, keywords)
            rows = await build_rows(source, candidates)

            if rows:
                logger.info("worker.inserted source=%s rows=%d", source, len(rows))
                logger.info(
                    "debug.printrow \n\tsource=%s\n\ttitle=%s\n\tbody=%s\n\tsentiment=%s",
                    rows[0][2],
                    rows[0][3],
                    rows[0][4],
                    rows[0][5],
                )
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
    load_sentiment_pipeline()
    logger.info("engine.start configs=%d", len(CONFIGS))

    # Phase 2 scaling: move sentiment inference to a worker queue/microservice
    # (e.g., Celery/RabbitMQ or an HTTP model service) to isolate ML latency.

    # async with aiohttp.ClientSession() as session:
    #     tasks = [asyncio.create_task(ingest_loop_debug(session, config)) for config in CONFIGS]
    #     await asyncio.gather(*tasks)

    pool = await asyncpg.create_pool(dsn=DB_DSN, min_size=1, max_size=10)
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(ingest_loop(pool, session, config)) for config in CONFIGS]
        await asyncio.gather(*tasks)
    await pool.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("engine.shutdown")
