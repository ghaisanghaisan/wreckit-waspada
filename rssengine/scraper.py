from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import aiohttp
import feedparser


@dataclass(frozen=True)
class Candidate:
    url: str
    title: str
    body: str
    published_at: datetime


def normalize_keywords(keywords: List[str]) -> List[str]:
    return [keyword.strip().lower() for keyword in keywords if keyword and keyword.strip()]


def is_relevant(title: str, body: str, keywords: List[str]) -> bool:
    if not keywords:
        return True
    haystack = f"{title} {body}".lower()
    return any(keyword in haystack for keyword in keywords)


def extract_body(entry) -> str:
    if "content" in entry and entry.content:
        value = getattr(entry.content[0], "value", None)
        if value:
            return value
    summary = getattr(entry, "summary", None)
    return summary or ""


def to_utc_datetime(parsed_time) -> datetime | None:
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


async def fetch_xml(
    session: aiohttp.ClientSession,
    url: str,
    timeout_seconds: int,
    retries: int,
    backoff_base: float,
    user_agent: str,
    logger,
) -> str:
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    headers = {"User-Agent": user_agent}
    last_exc: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, timeout=timeout, headers=headers) as response:
                response.raise_for_status()
                return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            backoff = backoff_base ** (attempt - 1)
            logger.warning(
                "fetch.retry url=%s attempt=%d/%d error=%s backoff=%.2fs",
                url,
                attempt,
                retries,
                type(exc).__name__,
                backoff,
            )
            if attempt < retries:
                await asyncio.sleep(backoff)

    logger.exception("fetch.failed url=%s attempts=%d", url, retries)
    raise last_exc or RuntimeError("fetch failed")


async def parse_feed(raw_xml: str):
    return await asyncio.to_thread(feedparser.parse, raw_xml)


def collect_candidates(feed, keywords: List[str]) -> List[Candidate]:
    now = datetime.now(timezone.utc)
    normalized = normalize_keywords(keywords)
    candidates: List[Candidate] = []
    for entry in feed.entries:
        url = getattr(entry, "link", None)
        if not url:
            continue
        title = getattr(entry, "title", "") or ""
        body = extract_body(entry)
        if not is_relevant(title, body, normalized):
            continue
        published_at = (
            to_utc_datetime(getattr(entry, "published_parsed", None))
            or to_utc_datetime(getattr(entry, "updated_parsed", None))
            or now
        )
        candidates.append(Candidate(url=url, title=title, body=body, published_at=published_at))
    return candidates