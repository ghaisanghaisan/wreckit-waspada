from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timezone
from typing import Any

from .config import AppConfig

logger = logging.getLogger("waspada.rss_engine.reporting")

MAX_CONTENT_CHARS = 25000
DEFAULT_NO_TASK_SLEEP_SECONDS = 30
GROQ_MODEL_NAME = "llama3-70b-8192"


async def weekly_report_worker(config: AppConfig, pool) -> None:
    interval = int(config.weekly_report_interval_seconds)
    task = asyncio.current_task()
    task_name = getattr(task, "get_name", lambda: None)()
    logger.info(
        "weekly_report.start interval=%s task=%s",
        interval,
        task_name,
    )

    while True:
        logger.info("weekly_report.poll")
        report_request = await _claim_pending_report(pool)

        if report_request is None:
            logger.debug("weekly_report.no_pending")
            if config.run_once:
                logger.info("weekly_report.exit_once no pending requests")
                break
            await _sleep_with_jitter(DEFAULT_NO_TASK_SLEEP_SECONDS)
            continue

        request_id = report_request["id"]
        organization_id = str(report_request.get("organization_id", ""))
        url_list = list(report_request.get("urls") or [])

        logger.info(
            "weekly_report.claimed request_id=%s organization_id=%s urls=%s",
            request_id,
            organization_id,
            len(url_list),
        )

        if not url_list:
            logger.warning("weekly_report.empty_urls request_id=%s", request_id)
            await _finalize_report_request(pool, request_id, "FAILED", "No URLs provided for report request.")
            if config.run_once:
                break
            continue

        article_texts = await asyncio.gather(*[_scrape_url(url) for url in url_list])
        filtered_texts = [text for text in article_texts if isinstance(text, str) and text.strip()]

        if not filtered_texts:
            logger.warning("weekly_report.no_scraped_text request_id=%s", request_id)
            await _finalize_report_request(pool, request_id, "FAILED", "No article text could be scraped from provided URLs.")
            if config.run_once:
                break
            continue

        combined_text = _combine_texts(filtered_texts, MAX_CONTENT_CHARS)
        logger.info(
            "weekly_report.combined_text request_id=%s combined_length=%s",
            request_id,
            len(combined_text),
        )

        try:
            markdown_report = await _generate_markdown_summary(combined_text)
            await _finalize_report_request(pool, request_id, "COMPLETED", markdown_report)
            logger.info("weekly_report.completed request_id=%s", request_id)
        except Exception as exc:
            logger.exception("weekly_report.failed request_id=%s", request_id)
            await _finalize_report_request(
                pool,
                request_id,
                "FAILED",
                f"Report generation failed: {type(exc).__name__}: {exc}",
            )

        if config.run_once:
            logger.info("weekly_report.exit_once completed request_id=%s", request_id)
            break

        await _sleep_with_jitter(interval)


async def _claim_pending_report(pool) -> dict[str, Any] | None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT id, organization_id, urls
                FROM report_requests
                WHERE status = 'PENDING'
                ORDER BY requested_at ASC NULLS LAST
                FOR UPDATE SKIP LOCKED
                LIMIT 1
                """,
            )
            if row is None:
                return None
            await conn.execute(
                "UPDATE report_requests SET status = 'IN_PROGRESS', updated_at = now() WHERE id = $1",
                row["id"],
            )
            return dict(row)


async def _finalize_report_request(pool, request_id: Any, status: str, result_text: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE report_requests SET status = $1, generated_report = $2, updated_at = now() WHERE id = $3",
            status,
            result_text,
            request_id,
        )


async def _scrape_url(url: str) -> str:
    try:
        import trafilatura

        raw_html = await asyncio.to_thread(trafilatura.fetch_url, url, timeout=20)
        if not raw_html:
            logger.warning("weekly_report.scrape_empty url=%s", url)
            return ""

        extracted = await asyncio.to_thread(
            trafilatura.extract,
            raw_html,
            output_format="text",
            include_comments=False,
            include_tables=False,
        )
        return extracted.strip() if isinstance(extracted, str) else ""
    except Exception as exc:
        logger.warning("weekly_report.scrape_error url=%s error=%s", url, exc, exc_info=True)
        return ""


def _combine_texts(texts: list[str], max_chars: int) -> str:
    combined_parts: list[str] = []
    total = 0
    for text in texts:
        if not text:
            continue
        if total + len(text) + 2 > max_chars:
            remaining = max_chars - total
            if remaining > 0:
                combined_parts.append(text[:remaining].rstrip())
            break
        combined_parts.append(text)
        total += len(text) + 2
    return "\n\n".join(combined_parts).strip()


async def _generate_markdown_summary(combined_text: str) -> str:
    from groq import AsyncGroq

    system_prompt = """
    Anda adalah analis intelijen senior yang bertugas menyusun laporan situasional mingguan untuk pimpinan tingkat strategis.

    Analisis seluruh kumpulan artikel yang diberikan dan identifikasi perkembangan paling signifikan, tren utama, aktor yang terlibat, risiko yang muncul, serta implikasinya terhadap organisasi atau pengambil keputusan.

    Fokus pada sintesis informasi, bukan sekadar ringkasan artikel. Gabungkan informasi yang saling terkait menjadi tema-tema utama dan prioritaskan isu berdasarkan dampak, frekuensi kemunculan, dan urgensi.

    Gunakan bahasa formal, objektif, dan berbasis fakta. Hindari spekulasi yang tidak didukung data. Jika terdapat ketidakpastian, jelaskan secara singkat tingkat keyakinan analisis.

    Tujuan utama Anda adalah menghasilkan laporan yang dapat dibaca langsung oleh pimpinan untuk memahami situasi secara cepat dan mengambil keputusan yang tepat.

    Keluaran HARUS berupa Markdown yang terstruktur dengan baik.

    Gunakan format Markdown berikut:

    # Ringkasan Eksekutif
    - 3–5 temuan paling penting.
    - Fokus pada informasi yang paling relevan bagi pimpinan.

    # Tren Utama
    ## Tren 1
    - Deskripsi
    - Bukti Pendukung
    - Implikasi

    ## Tren 2
    - Deskripsi
    - Bukti Pendukung
    - Implikasi

    # Peristiwa Penting
    | Peristiwa | Signifikansi | Dampak |
    |------------|--------------|---------|

    # Risiko dan Ancaman yang Muncul
    | Risiko | Tingkat Risiko | Analisis | Dampak Potensial |
    |----------|---------------|-----------|------------------|

    Tingkat Risiko yang diperbolehkan:
    - Rendah
    - Sedang
    - Tinggi
    - Kritis

    # Aktor dan Entitas Kunci
    | Entitas | Peran | Signifikansi |
    |----------|--------|-------------|

    # Implikasi Strategis
    - ...

    # Indikator Peringatan Dini
    - ...

    # Area Pemantauan Minggu Depan
    - ...

    Pastikan laporan:
    - Ringkas namun informatif.
    - Tidak mengulang informasi yang sama.
    - Memprioritaskan isu berdasarkan dampak dan urgensi.
    - Menggunakan bahasa formal dan profesional.
    - Menyoroti perubahan dibandingkan pola yang dominan dalam kumpulan artikel.
    """

    user_prompt = f"""
    Analisis kumpulan artikel berikut dan susun satu laporan intelijen mingguan tingkat strategis.

    Instruksi Analisis:
    1. Identifikasi tren utama yang berkembang selama periode pelaporan.
    2. Soroti peristiwa penting yang memiliki dampak signifikan.
    3. Identifikasi risiko, ancaman, atau potensi eskalasi yang mulai muncul.
    4. Kelompokkan informasi yang saling berkaitan menjadi tema-tema utama.
    5. Identifikasi aktor, organisasi, institusi, atau tokoh yang paling relevan.
    6. Jelaskan implikasi strategis yang perlu diperhatikan oleh pengambil keputusan.
    7. Berikan area pemantauan dan indikator peringatan dini (early warning indicators) untuk minggu berikutnya.


    Berikut adalah kumpulan artikel yang perlu dianalisis:

    {combined_text}
    """

    async with AsyncGroq() as client:
        response = await client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_output_tokens=1024,
        )

    return _extract_response_text(response)


def _extract_response_text(response: Any) -> str:
    if response is None:
        return ""

    if isinstance(response, dict):
        if "output" in response:
            output = response["output"]
        elif "text" in response:
            output = response["text"]
        else:
            output = response
    else:
        output = getattr(response, "output", None) or getattr(response, "text", None) or response

    if isinstance(output, str):
        return output.strip()
    if isinstance(output, list):
        parts = []
        for item in output:
            if isinstance(item, dict):
                parts.append(str(item.get("content", "")))
            else:
                parts.append(str(item))
        return "\n".join(parts).strip()

    return str(output).strip()


async def _sleep_with_jitter(base_seconds: int) -> None:
    await asyncio.sleep(base_seconds + random.uniform(0, 1.0))
