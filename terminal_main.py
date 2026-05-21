"""Terminal entry point for the SEO crawler."""

import asyncio
import html
import os
import sys

from cli.prompt import prompt_domain
from config import DB_NAME, MAX_PAGES_WHOLE_SITE
from crawler import CrawlState, evaluate_crawl_result, run_crawler
from db.repository import find_domain_by_name
from models.schema import DOMAINS_COLLECTION, PAGES_COLLECTION
from storage import file_storage
from utils.logging_config import setup_logging

import logging

logger = logging.getLogger(__name__)


def write_crawl_summary_html(state: CrawlState, warnings: list[str]) -> str:
    domain_doc = find_domain_by_name(state.allowed_host) or {}
    os.makedirs(file_storage.domain_html_dir(state.allowed_host), exist_ok=True)
    path = file_storage.crawl_summary_html_path(state.allowed_host)

    def row(label: str, value: str) -> str:
        return f"<tr><th>{html.escape(label)}</th><td>{html.escape(value)}</td></tr>"

    url_list = "\n".join(f"<li>{html.escape(u)}</li>" for u in state.crawled_urls)
    dup_list = "\n".join(f"<li>{html.escape(u)}</li>" for u in state.duplicate_urls)
    fail_list = "\n".join(f"<li>{html.escape(u)}</li>" for u in state.failed_urls)
    warn_list = "\n".join(f"<li>{html.escape(w)}</li>" for w in warnings)

    body = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Crawl summary</title></head>
<body>
<h1>Crawl summary</h1>
<table border="1" cellspacing="0" cellpadding="4">
{row("domain_id", str(state.domain_id or ""))}
{row("total_pages_crawled (this run)", str(state.page_counter))}
{row("total_pages_in_mongodb (pages docs)", str(domain_doc.get("total_pages", 0)))}
{row("total_urls_crawled (success + failed, this run)", str(domain_doc.get("total_urls_crawled", "")))}
{row("crawled_pages (MongoDB)", str(domain_doc.get("crawled_pages", "")))}
{row("failed_pages (MongoDB)", str(domain_doc.get("failed_pages", "")))}
{row("total_duplicates_found", str(len(state.duplicate_urls)))}
{row("total_failed_requests", str(state.total_failures))}
{row("total_retries", str(state.total_retries))}
{row("total_fallbacks", str(state.total_fallbacks))}
{row("mongo_failures", str(state.mongo_failures))}
{row("off_domain_skipped", str(state.off_domain_skipped))}
{row("mongodb_database", DB_NAME)}
{row("mongodb_collections", f"{DOMAINS_COLLECTION}, {PAGES_COLLECTION}")}
{row("crawl_mode", state.crawl_mode)}
{row("max_pages_limit", str(state.max_pages) if state.max_pages > 0 else "unlimited")}
{row("start_url", state.seed_url)}
</table>
<h2>Warnings</h2>
<ul>{warn_list or "<li>(none)</li>"}</ul>
<h2>Crawled URLs</h2>
<ul>{url_list or "<li>(none)</li>"}</ul>
<h2>Duplicate URLs</h2>
<ul>{dup_list or "<li>(none)</li>"}</ul>
<h2>Failed URLs</h2>
<ul>{fail_list or "<li>(none)</li>"}</ul>
</body></html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def main() -> int:
    setup_logging()
    print("SEO Crawler POC (Crawlee + Playwright → HTTP fallback)\n")

    try:
        seed_url, allowed_host = prompt_domain()
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2

    max_pages = MAX_PAGES_WHOLE_SITE
    crawl_mode = "whole_site"
    page_limit_label = str(max_pages) if max_pages > 0 else "unlimited (all same-domain pages)"
    print(f"\nSeed URL:   {seed_url}")
    print(f"Domain:     {allowed_host}")
    print(f"Page limit: {page_limit_label}")
    print(f"HTML dir:   {file_storage.domain_html_dir(allowed_host)}/")
    print(f"MongoDB:    {DB_NAME} ({DOMAINS_COLLECTION}, {PAGES_COLLECTION})\n")

    try:
        state = asyncio.run(
            run_crawler(seed_url, allowed_host, max_pages, crawl_mode=crawl_mode)
        )
    except Exception as exc:
        logger.exception("Crawl failed")
        print(f"\nFatal: {exc}")
        print("Is MongoDB running on mongodb://localhost:27017 ?")
        return 1

    ok, warnings = evaluate_crawl_result(state)
    summary_path = write_crawl_summary_html(state, warnings)

    domain_doc = find_domain_by_name(allowed_host) or {}
    total_in_mongo = domain_doc.get("total_pages", 0)
    total_urls_run = domain_doc.get("total_urls_crawled")

    print("Done.")
    print(f"  Domain ID:  {state.domain_id}")
    print(f"  Pages:      {state.page_counter}")
    print(f"  Total pages (MongoDB domains, pages coll count): {total_in_mongo}")
    print(f"  Total URLs this run (success+fail, domains): {total_urls_run}")
    print(f"  Duplicates: {len(state.duplicate_urls)}")
    print(f"  Failed:     {state.total_failures}")
    print(f"  Retries:    {state.total_retries}")
    print(f"  Fallbacks:  {state.total_fallbacks}")
    print(f"  Mongo err:  {state.mongo_failures}")
    print(f"  Summary:    {summary_path}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    if not ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
