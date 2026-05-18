from __future__ import annotations

from dataclasses import dataclass
import os
from typing import List, Optional


@dataclass(frozen=True)
class RSSSourceConfig:
    source: str
    url: str
    interval_seconds: int
    keywords: Optional[List[str]] = None


@dataclass(frozen=True)
class AppConfig:
    db_dsn: str
    sources: List[RSSSourceConfig]
    global_keywords: List[str]
    run_once: bool
    request_timeout_seconds: int
    fetch_retries: int
    fetch_backoff_base: float
    user_agent: str
    model_name: str
    sentiment_labels: List[str]
    sentiment_min_confidence: float
    sentiment_max_concurrency: int
    sentiment_batch_size: int
    url_cache_maxlen: int


GLOBAL_KEYWORDS: List[str] = [
    "Polri",
    "Polisi",
    "Mabes Polri",
    "Kepolisian Negara Republik Indonesia",
    "Korps Bhayangkara",
    "Polda",
    "Polres",
    "Polresta",
    "Polsek",
    "Kapolri",
    "Wakapolri",
    "Kapolda",
    "Kapolres",
    "Kapolsek",
    "Kadiv Humas Polri",
    "Bareskrim",
    "Korlantas",
    "Brimob",
    "Densus 88",
    "Propam",
    "Ditlantas",
    "Ditreskrimsus",
    "Ditreskrimum",
    "Polda Metro Jaya",
    "Kamtibmas",
    "Operasi Ketupat",
    "Operasi Lilin",
    "Operasi Zebra",
    "Tilang elektronik",
    "ETLE",
    "Samsat",
    "SIM Keliling",
]

SENTIMENT_POSITIVE = (
    "apresiasi masyarakat, dukungan publik, kepuasan warga, pujian, kepercayaan publik, "
    "respons positif, pelayanan memuaskan, citra baik, pro-rakyat, antusiasme, kebanggaan, "
    "simpati masyarakat, sambutan hangat, harapan baru, kinerja gemilang, inovasi bermanfaat, "
    "keberpihakan pada rakyat, solusi tepat sasaran, dukungan netizen"
)
SENTIMENT_NEGATIVE = (
    "kekecewaan publik, kritik tajam, penolakan warga, protes masyarakat, kecaman, krisis kepercayaan, "
    "kinerja buruk, ketidakpuasan, tuntutan, desakan mundur, viral negatif, kemarahan netizen, "
    "keresahan warga, polemik berkepanjangan, kontroversi, rapor merah, skeptisisme, "
    "dugaan penyelewengan, kecurigaan publik, reaksi keras, blunder"
)
SENTIMENT_NEUTRAL = (
    "pengumuman resmi, sosialisasi kebijakan, agenda kegiatan, informasi faktual, laporan rutin, "
    "pernyataan prosedural, data statistik, regulasi pemerintah, kunjungan kerja, peresmian fasilitas, "
    "pelantikan pejabat, tata kelola birokrasi, seremonial, jadwal pelaksanaan, rilis pers, liputan langsung"
)


def load_config() -> AppConfig:
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_pass = os.getenv("POSTGRES_PASSWORD", "gulingkanan")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "waspada")
    db_dsn = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    sources = [
        RSSSourceConfig(
            source="antaranews.com",
            url="https://www.antaranews.com/rss/top-news",
            interval_seconds=10,
        ),
        RSSSourceConfig(
            source="liputan6.com",
            url="https://feed.liputan6.com/rss/news",
            interval_seconds=10,
        ),
        RSSSourceConfig(
            source="cnnindonesia.com",
            url="https://www.cnnindonesia.com/nasional/rss",
            interval_seconds=10,
        ),
        RSSSourceConfig(
            source="cnbcindonesia.com",
            url="https://www.cnbcindonesia.com/news/rss",
            interval_seconds=10,
        ),
    ]

    sentiment_labels = [SENTIMENT_POSITIVE, SENTIMENT_NEGATIVE, SENTIMENT_NEUTRAL]

    return AppConfig(
        db_dsn=db_dsn,
        sources=sources,
        global_keywords=GLOBAL_KEYWORDS,
        run_once=os.getenv("RUN_ONCE", "0") == "1",
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
        fetch_retries=int(os.getenv("FETCH_RETRIES", "3")),
        fetch_backoff_base=float(os.getenv("FETCH_BACKOFF_BASE", "1.5")),
        user_agent=os.getenv("USER_AGENT", "waspada-rss-bot/1.0"),
        model_name=os.getenv(
            "SENTIMENT_MODEL_NAME",
            "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        ),
        sentiment_labels=sentiment_labels,
        sentiment_min_confidence=float(os.getenv("SENTIMENT_MIN_CONFIDENCE", "0.4")),
        sentiment_max_concurrency=int(os.getenv("SENTIMENT_MAX_CONCURRENCY", "2")),
        sentiment_batch_size=int(os.getenv("SENTIMENT_BATCH_SIZE", "16")),
        url_cache_maxlen=int(os.getenv("URL_CACHE_MAXLEN", "500")),
    )