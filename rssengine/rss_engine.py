import asyncio
import logging
import os
import uuid
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

logger = logging.getLogger("waspada.rss_engine")

SENTIMENT_PIPELINE = None
SENTIMENT_POSITIVE = "apresiasi masyarakat, dukungan publik, kepuasan warga, pujian, kepercayaan publik, respons positif, pelayanan memuaskan, citra baik, pro-rakyat, antusiasme, kebanggaan, simpati masyarakat, sambutan hangat, harapan baru, kinerja gemilang, inovasi bermanfaat, keberpihakan pada rakyat, solusi tepat sasaran, dukungan netizen"
SENTIMENT_NEGATIVE = "kekecewaan publik, kritik tajam, penolakan warga, protes masyarakat, kecaman, krisis kepercayaan, kinerja buruk, ketidakpuasan, tuntutan, desakan mundur, viral negatif, kemarahan netizen, keresahan warga, polemik berkepanjangan, kontroversi, rapor merah, skeptisisme, dugaan penyelewengan, kecurigaan publik, reaksi keras, blunder"
SENTIMENT_NEUTRAL = "pengumuman resmi, sosialisasi kebijakan, agenda kegiatan, informasi faktual, laporan rutin, pernyataan prosedural, data statistik, regulasi pemerintah, kunjungan kerja, peresmian fasilitas, pelantikan pejabat, tata kelola birokrasi, seremonial, jadwal pelaksanaan, rilis pers, liputan langsung"

SENTIMENT_LABELS = [SENTIMENT_POSITIVE, SENTIMENT_NEGATIVE, SENTIMENT_NEUTRAL]

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


async def build_rows(source: str, feed, keywords: list[str]) -> list[tuple]:
    now = datetime.now(timezone.utc)
    normalized_keywords = normalize_keywords(keywords)
    rows = []
    sentiment_tasks = []
    for entry in feed.entries:
        url = getattr(entry, "link", None)
        if not url:
            continue

        title = getattr(entry, "title", "") or ""
        body = extract_body(entry)

        if not is_relevant(title, body, normalized_keywords):
            continue

        text = f"{title} {body}".strip()
        sentiment_tasks.append(asyncio.to_thread(classify_sentiment, text))

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
    if sentiment_tasks:
        sentiments = await asyncio.gather(*sentiment_tasks)
        enriched_rows = []
        for row, sentiment in zip(rows, sentiments):
            enriched_rows.append(
                (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    sentiment,
                    row[5],
                    row[6],
                )
            )
        return enriched_rows
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
            rows = await build_rows(source, feed, keywords)
            fetched = len(feed.entries)
            passed = len(rows)
            if rows:
                positives = sum(1 for row in rows if row[5] == "POSITIF")
                negatives = len(rows) - positives
                logger.info(
                    "sentiment.analyzed source=%s total=%d positif=%d negatif=%d",
                    source,
                    len(rows),
                    positives,
                    negatives,
                )

            if rows:
                async with pool.acquire() as conn:
                    await conn.executemany(UPSERT_SQL, rows)
                logger.info(
                    "worker.inserted source=%s fetched=%d passed=%d inserted=%d",
                    source,
                    fetched,
                    passed,
                    len(rows),
                )
            else:
                logger.info(
                    "worker.empty source=%s fetched=%d passed=%d",
                    source,
                    fetched,
                    passed,
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
            rows = await build_rows(source, feed, keywords)

            if rows:
                # async with pool.acquire() as conn:
                #     await conn.executemany(UPSERT_SQL, rows)
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
