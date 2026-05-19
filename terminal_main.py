"""Terminal entry point for the SEO crawler."""

import asyncio
import json
import sys

from cli.prompt import prompt_domain
from config import DB_NAME, MAX_PAGES_WHOLE_SITE
from crawler import CrawlState, evaluate_crawl_result, run_crawler
from models.schema import DOMAINS_COLLECTION, PAGES_COLLECTION
from storage import file_storage
from utils.logging_config import setup_logging

import logging

logger = logging.getLogger(__name__)


def write_summary(state: CrawlState, warnings: list[str]) -> str:
    summary = {
        "domain_id": state.domain_id,
        "total_pages_crawled": state.page_counter,
        "total_duplicates_found": len(state.duplicate_urls),
        "total_failed_requests": state.total_failures,
        "total_retries": state.total_retries,
        "total_fallbacks": state.total_fallbacks,
        "mongo_failures": state.mongo_failures,
        "off_domain_skipped": state.off_domain_skipped,
        "warnings": warnings,
        "mongodb_database": DB_NAME,
        "mongodb_collections": [DOMAINS_COLLECTION, PAGES_COLLECTION],
        "crawl_mode": state.crawl_mode,
        "max_pages_limit": state.max_pages,
        "start_url": state.seed_url,
        "list_of_urls": state.crawled_urls,
        "list_of_duplicate_urls": state.duplicate_urls,
        "list_of_failed_urls": state.failed_urls,
    }
    path = file_storage.summary_path(state.allowed_host)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
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
    print(f"\nSeed URL:   {seed_url}")
    print(f"Domain:     {allowed_host}")
    print(f"Max pages:  {max_pages}")
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
    summary_path = write_summary(state, warnings)

    print("Done.")
    print(f"  Domain ID:  {state.domain_id}")
    print(f"  Pages:      {state.page_counter}")
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
