"""Backward-compatible re-exports; use db.repository."""

from config import DB_NAME
from db.repository import (
    find_domain_by_name,
    find_page_by_url,
    finish_domain_crawl,
    ping,
    save_page,
    start_domain_crawl,
)
from models.schema import DOMAINS_COLLECTION, PAGES_COLLECTION

__all__ = [
    "DB_NAME",
    "DOMAINS_COLLECTION",
    "PAGES_COLLECTION",
    "find_domain_by_name",
    "find_page_by_url",
    "finish_domain_crawl",
    "ping",
    "save_page",
    "start_domain_crawl",
]
