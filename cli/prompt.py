"""Terminal input for domain / URL and crawl scope."""

from config import MAX_PAGES, MAX_PAGES_WHOLE_SITE
from utils.url_utils import parse_user_input


def prompt_domain() -> tuple[str, str]:
    """Read and validate crawl target from stdin. Returns (seed_url, allowed_host)."""
    raw = input("Enter domain or URL to crawl (e.g. example.com): ").strip()
    return parse_user_input(raw)


def prompt_crawl_scope() -> tuple[int, str]:
    """
    Ask whether to crawl up to MAX_PAGES or whole site (capped by MAX_PAGES_WHOLE_SITE).
    Returns (max_pages, crawl_mode) where crawl_mode is 'limited' or 'whole_site'.
    """
    print("\nCrawl scope:")
    print(f"  1 - Limited (max {MAX_PAGES} pages)")
    print(f"  2 - Whole site (all discoverable pages, max {MAX_PAGES_WHOLE_SITE})")
    while True:
        choice = input("Choose 1 or 2 [1]: ").strip() or "1"
        if choice == "1":
            return MAX_PAGES, "limited"
        if choice == "2":
            return MAX_PAGES_WHOLE_SITE, "whole_site"
        print("Invalid choice. Enter 1 or 2.")
