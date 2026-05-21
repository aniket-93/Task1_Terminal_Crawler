"""Crawlee Playwright crawler with HTTP fallback."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta

import httpx
from crawlee import ConcurrencySettings, Request
from crawlee.configuration import Configuration
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

from config import (
    CRAWLEE_PURGE_ON_START,
    HEADLESS,
    IGNORE_HTTP_STATUS_CODES,
    MAX_BODY_BYTES,
    MAX_CONCURRENCY,
    MAX_PAGES_WHOLE_SITE,
    MAX_RETRIES,
    MIN_HTML_BYTES,
    REQUEST_DELAY_MS,
    REQUEST_TIMEOUT_SEC,
    USER_AGENT,
)
from db.repository import (
    finish_domain_crawl,
    ping,
    save_failed_page,
    save_page,
    start_domain_crawl,
)
from models import build_seo_page_record
from parser import extract_links, parse_seo
from storage import file_storage
from utils.security import is_safe_crawl_target
from utils.url_utils import is_same_domain, normalize_url

logger = logging.getLogger(__name__)

USER_DEPTH = "depth"
USER_SOURCE = "source_url"
# Crawlee requires a numeric cap; used only when max_pages is 0 (unlimited).
UNLIMITED_MAX_REQUESTS = 10_000_000


def _page_limit_reached(state: CrawlState) -> bool:
    return state.max_pages > 0 and state.page_counter >= state.max_pages


def _max_requests_for_crawl(max_pages: int) -> int:
    return max_pages * 5 if max_pages > 0 else UNLIMITED_MAX_REQUESTS


@dataclass
class CrawlState:
    """Per-run crawl statistics and URL tracking."""

    allowed_host: str
    max_pages: int = MAX_PAGES_WHOLE_SITE
    crawl_mode: str = "whole_site"
    domain_id: str | None = None
    seed_url: str = ""
    visited_urls: set[str] = field(default_factory=set)
    enqueued_urls: set[str] = field(default_factory=set)
    duplicate_urls: list[str] = field(default_factory=list)
    failed_urls: list[str] = field(default_factory=list)
    crawled_urls: list[str] = field(default_factory=list)
    page_counter: int = 0
    total_retries: int = 0
    total_failures: int = 0
    total_fallbacks: int = 0
    mongo_failures: int = 0
    off_domain_skipped: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


def evaluate_crawl_result(state: CrawlState) -> tuple[bool, list[str]]:
    """
    Purpose: Decide if crawl is successful and collect user-facing warnings.
    Outputs: (success, warning messages).
    """
    warnings: list[str] = []
    if state.page_counter == 0:
        warnings.append("No pages were crawled.")
    if state.mongo_failures > 0:
        warnings.append(
            f"MongoDB save failed for {state.mongo_failures} page(s); check logs/crawler.log."
        )
    if state.total_failures > 0:
        warnings.append(f"{state.total_failures} URL(s) failed after retries.")
    success = state.page_counter > 0
    return success, warnings


def _retryable_status(status: int | None) -> bool:
    """Retry only on server/rate-limit errors, not on missing status with body."""
    if status is None:
        return False
    if status == 429:
        return True
    return 500 <= status < 600


def _is_valid_html(html: str | None) -> bool:
    if not html or not html.strip():
        return False
    return len(html.encode("utf-8", errors="replace")) >= MIN_HTML_BYTES


def _final_url(context: PlaywrightCrawlingContext) -> str:
    loaded = context.request.loaded_url or context.page.url or context.request.url
    return normalize_url(loaded)


def _log_duplicate(state: CrawlState, url: str) -> None:
    if url not in state.duplicate_urls:
        state.duplicate_urls.append(url)
    logger.debug("Duplicate URL skipped: %s", url)


async def _sleep_delay() -> None:
    await asyncio.sleep(REQUEST_DELAY_MS / 1000.0)


async def _fetch_http(url: str) -> tuple[str | None, int | None]:
    headers = {"User-Agent": USER_AGENT}
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SEC)
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, headers=headers) as client:
        resp = await client.get(url)
        body = resp.text
        if len(body.encode("utf-8", errors="replace")) > MAX_BODY_BYTES:
            logger.warning("HTTP body too large: %s", url)
            return None, resp.status_code
        return body, resp.status_code


async def _fetch_playwright(context: PlaywrightCrawlingContext) -> tuple[str | None, int | None]:
    context.page.set_default_timeout(REQUEST_TIMEOUT_SEC * 1000)
    await context.page.wait_for_load_state("domcontentloaded", timeout=REQUEST_TIMEOUT_SEC * 1000)
    html = await context.page.content()
    status = context.response.status if context.response else None
    if len(html.encode("utf-8", errors="replace")) > MAX_BODY_BYTES:
        logger.warning("Playwright body too large: %s", context.request.url)
        return None, status
    return html, status


async def _fetch_with_fallback(
    context: PlaywrightCrawlingContext, url: str, state: CrawlState
) -> tuple[str | None, int | None, str]:
    try:
        html, status = await _fetch_playwright(context)
        if _is_valid_html(html):
            return html, status if status is not None else 200, "playwright"
    except Exception as exc:
        logger.warning("Playwright failed for %s: %s", url, exc)

    async with state.lock:
        state.total_fallbacks += 1
    logger.warning("Fallback to HTTP for %s", url)
    try:
        html, status = await _fetch_http(url)
        if _is_valid_html(html):
            return html, status if status is not None else 200, "http_fallback"
    except Exception as exc:
        logger.error("HTTP fallback failed for %s: %s", url, exc)
    return None, None, "failed"


async def _persist_page(
    state: CrawlState,
    url: str,
    html: str,
    status: int | None,
    retry_count: int,
    fetch_method: str,
) -> bool:
    async with state.lock:
        if _page_limit_reached(state):
            return False
        state.page_counter += 1
        page_num = state.page_counter

    norm = normalize_url(url)
    status_code = int(status) if status is not None else 200
    html_path = file_storage.html_path_for_save(state.allowed_host, url)
    html_path_for_db = file_storage.relative_html_path(state.allowed_host, url)

    try:
        file_storage.save_html(html_path, html)
    except OSError as exc:
        logger.error("HTML save failed for %s: %s", url, exc)
        async with state.lock:
            state.page_counter -= 1
        return False

    seo = parse_seo(url, norm, html, status_code, html_path_for_db)
    record = build_seo_page_record(
        seo,
        domain=state.allowed_host,
        fetch_method=fetch_method,
        retry_count=retry_count,
    )

    if not state.domain_id or not save_page(state.domain_id, record):
        async with state.lock:
            state.mongo_failures += 1

    async with state.lock:
        state.visited_urls.add(norm)
        state.crawled_urls.append(url)

    page_label = f"{page_num}/{state.max_pages}" if state.max_pages > 0 else str(page_num)
    logger.info(
        "Page %s | %s | status=%s | %s | %s",
        page_label,
        url,
        status_code,
        fetch_method,
        html_path_for_db,
    )
    if status_code != 200:
        logger.warning("Non-200 status %s for %s", status_code, url)
    return True


async def _mark_failed(state: CrawlState, url: str, error: str = "fetch failed after retries") -> None:
    norm = normalize_url(url)
    async with state.lock:
        state.visited_urls.add(norm)
        state.total_failures += 1
        if url not in state.failed_urls:
            state.failed_urls.append(url)
    if state.domain_id:
        save_failed_page(state.domain_id, state.allowed_host, url, error)
    logger.error("Failed URL: %s (%s)", url, error)


async def _enqueue_links(
    state: CrawlState,
    html: str,
    page_url: str,
    depth: int,
    add_requests,
) -> None:
    async with state.lock:
        if _page_limit_reached(state):
            return

    batch: list[Request] = []
    for link in extract_links(html, page_url, state.allowed_host):
        if not is_safe_crawl_target(link):
            continue
        norm = normalize_url(link)
        async with state.lock:
            if norm in state.visited_urls or norm in state.enqueued_urls:
                _log_duplicate(state, norm)
                continue
            if _page_limit_reached(state):
                return
            state.enqueued_urls.add(norm)
        batch.append(
            Request.from_url(link, user_data={USER_DEPTH: depth + 1, USER_SOURCE: page_url})
        )
    if batch:
        await add_requests(batch)


async def run_crawler(
    seed_url: str,
    allowed_host: str,
    max_pages: int = MAX_PAGES_WHOLE_SITE,
    *,
    crawl_mode: str = "whole_site",
) -> CrawlState:
    ping()
    state = CrawlState(
        allowed_host=allowed_host,
        max_pages=max_pages,
        crawl_mode=crawl_mode,
        seed_url=seed_url,
    )
    seed_norm = normalize_url(seed_url)
    state.enqueued_urls.add(seed_norm)

    domain_id = start_domain_crawl(allowed_host, seed_url)
    state.domain_id = domain_id
    crawl_started_at = time.perf_counter()

    limit_label = str(max_pages) if max_pages > 0 else "unlimited"
    logger.info(
        "Crawl start | host=%s | domain_id=%s | page_limit=%s",
        allowed_host,
        domain_id,
        limit_label,
    )

    configuration = Configuration(purge_on_start=CRAWLEE_PURGE_ON_START)
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=_max_requests_for_crawl(max_pages),
        max_request_retries=MAX_RETRIES,
        headless=HEADLESS,
        configuration=configuration,
        ignore_http_error_status_codes=IGNORE_HTTP_STATUS_CODES,
        request_handler_timeout=timedelta(seconds=REQUEST_TIMEOUT_SEC * 2),
        concurrency_settings=ConcurrencySettings(
            min_concurrency=1,
            max_concurrency=MAX_CONCURRENCY,
            desired_concurrency=MAX_CONCURRENCY,
        ),
    )

    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext) -> None:
        request_url = normalize_url(context.request.url)
        depth = int(context.request.user_data.get(USER_DEPTH, 0) or 0)

        try:
            if not is_same_domain(request_url, state.allowed_host):
                return
            if not is_safe_crawl_target(request_url):
                logger.warning("Unsafe URL skipped: %s", request_url)
                return

            async with state.lock:
                if request_url in state.visited_urls:
                    _log_duplicate(state, request_url)
                    return
                if _page_limit_reached(state):
                    return

            await _sleep_delay()

            if context.request.retry_count > 0:
                async with state.lock:
                    state.total_retries += 1
                logger.warning("Retry %s for %s", context.request.retry_count, request_url)

            html, status, method = await _fetch_with_fallback(context, request_url, state)

            if not _is_valid_html(html):
                if context.request.retry_count < MAX_RETRIES:
                    async with state.lock:
                        state.total_retries += 1
                    raise RuntimeError(f"Fetch failed, retry: {request_url}")
                await _mark_failed(state, request_url)
                return

            final_url = _final_url(context)
            if not is_same_domain(final_url, state.allowed_host):
                async with state.lock:
                    state.off_domain_skipped += 1
                logger.warning(
                    "Off-domain after redirect: %s -> %s (skipped)",
                    request_url,
                    final_url,
                )
                return

            if _retryable_status(status) and context.request.retry_count < MAX_RETRIES:
                async with state.lock:
                    state.total_retries += 1
                raise RuntimeError(f"Retryable HTTP {status}: {request_url}")

            saved = await _persist_page(
                state,
                final_url,
                html,
                status,
                context.request.retry_count,
                method,
            )
            if saved:
                await _enqueue_links(state, html, final_url, depth, context.add_requests)

        except RuntimeError:
            raise
        except Exception as exc:
            logger.exception("Unhandled error for %s: %s", request_url, exc)
            if context.request.retry_count >= MAX_RETRIES:
                await _mark_failed(state, request_url)
            else:
                async with state.lock:
                    state.total_retries += 1
                raise

    try:
        await crawler.run(
            [Request.from_url(seed_norm, user_data={USER_DEPTH: 0, USER_SOURCE: None})]
        )
        ok, _ = evaluate_crawl_result(state)
        finish_domain_crawl(
            domain_id,
            "completed" if ok else "failed",
            crawled_pages=state.page_counter,
            failed_pages=state.total_failures,
            total_crawl_time=time.perf_counter() - crawl_started_at,
        )
    except Exception:
        finish_domain_crawl(
            domain_id,
            "failed",
            crawled_pages=state.page_counter,
            failed_pages=state.total_failures,
            total_crawl_time=time.perf_counter() - crawl_started_at,
        )
        raise

    logger.info(
        "Crawl end | pages=%s | dupes=%s | failed=%s | retries=%s | fallbacks=%s | mongo_err=%s",
        state.page_counter,
        len(state.duplicate_urls),
        state.total_failures,
        state.total_retries,
        state.total_fallbacks,
        state.mongo_failures,
    )
    return state
