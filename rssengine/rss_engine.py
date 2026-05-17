import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

import aiohttp
import asyncpg
import feedparser

DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'gulingkanan')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'waspada')

DB_DSN = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(DB_DSN)

keywords_polri = [
    # Nama Instansi & Singkatan
    "polri", 
    "Kementerian Pertahanan", 
    "Kemenhan", 
    "Kementerian Pertahanan Republik Indonesia", 
    "polri RI",
    
    # Jabatan & Pejabat
    "Menhan", 
    "Menteri Pertahanan", 
    "Wamenhan", 
    "Wakil Menteri Pertahanan", 
    "Sekjen polri", 
    "Dirjen polri",
    
    # Program Kerja & Isu Strategis
    "Alutsista", 
    "Modernisasi alutsista", 
    "Bela Negara", 
    "Komponen Cadangan", 
    "Komcad", 
    "Industri pertahanan", 
    "Anggaran polri", 
    "Ketahanan nasional", 
    "Diplomasi pertahanan",
    
    # Mitra & Institusi Terkait
    "polri TNI", 
    "Defend ID", 
    "PT Pindad", 
    "PT PAL", 
    "PT DI"
]
keywords_polri = [
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
        "keywords": keywords_polri,
    },
    {
        "source": "liputan6.com",
        "url": "https://feed.liputan6.com/rss/news",
        "interval_seconds": 10,
        "keywords": keywords_polri,
    },
    {
        "source": "cnnindonesia.com",
        "url": "https://www.cnnindonesia.com/nasional/rss",
        "interval_seconds": 10,
        "keywords": keywords_polri,
    },
    {
        "source": "cnbcindonesia.com",
        "url": "https://www.cnbcindonesia.com/news/rss",
        "interval_seconds": 10,
        "keywords": keywords_polri,
    },
]

RUN_ONCE = os.getenv("RUN_ONCE", "0") == "1"
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
FETCH_RETRIES = int(os.getenv("FETCH_RETRIES", "3"))
FETCH_BACKOFF_BASE = float(os.getenv("FETCH_BACKOFF_BASE", "1.5"))
USER_AGENT = os.getenv("USER_AGENT", "waspada-rss-bot/1.0")

logger = logging.getLogger("waspada.rss_engine")

UPSERT_SQL = """
INSERT INTO news_articles (
    id, url, source, title, body, published_at, scraped_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7
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


def build_rows(source: str, feed, keywords: list[str]) -> list[tuple]:
    now = datetime.now(timezone.utc)
    normalized_keywords = normalize_keywords(keywords)
    rows = []
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
    keywords = config.get("keywords", [])

    while True:
        logger.info("worker.wake source=%s url=%s", source, url)
        try:
            raw_xml = await fetch_xml(session, url)
            feed = await parse_feed(raw_xml)
            rows = build_rows(source, feed, keywords)
            fetched = len(feed.entries)
            passed = len(rows)

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

    while True:
        logger.info("worker.wake source=%s url=%s", source, url)
        try:
            raw_xml = await fetch_xml(session, url)
            feed = await parse_feed(raw_xml)
            rows = build_rows(source, feed)

            if rows:
                # async with pool.acquire() as conn:
                #     await conn.executemany(UPSERT_SQL, rows)
                logger.info("worker.inserted source=%s rows=%d", source, len(rows))
                logger.info("debug.printrow \n\tsource=%s\n\ttitle=%s\n\tbody=%s", rows[0][2], rows[0][3], rows[0][4])
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
