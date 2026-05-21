"""MongoDB: domains + pages collections."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from config import DB_NAME, MONGO_URI
from models.schema import (
    DOMAIN_FIELDS,
    DOMAIN_STATUSES,
    DOMAINS_COLLECTION,
    DOMAIN_INDEX_SPECS,
    PAGE_FIELDS,
    PAGE_INDEX_SPECS,
    PAGES_COLLECTION,
)
from models.seo_page import SeoPageRecord
from utils.url_utils import normalize_url, page_slug

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_indexes_ready: set[str] = set()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client


def _db():
    return get_client()[DB_NAME]


def domains_collection() -> Collection:
    return _db()[DOMAINS_COLLECTION]


def pages_collection() -> Collection:
    return _db()[PAGES_COLLECTION]


def _ensure_indexes() -> None:
    global _indexes_ready
    if _indexes_ready:
        return
    domains = domains_collection()
    pages = pages_collection()
    for field, opts in DOMAIN_INDEX_SPECS:
        domains.create_index(field, **opts)
    for field, opts in PAGE_INDEX_SPECS:
        if isinstance(field, tuple):
            pages.create_index(list(field), **opts)
        else:
            pages.create_index(field, **opts)
    _indexes_ready.add("ready")


def ping() -> None:
    get_client().admin.command("ping")
    _ensure_indexes()


def _object_id(domain_id: str) -> ObjectId:
    try:
        return ObjectId(domain_id)
    except InvalidId as exc:
        raise ValueError(f"invalid domain_id: {domain_id}") from exc


def start_domain_crawl(domain_name: str, start_url: str) -> str:
    """Create or reset domain row; return domain_id as string."""
    _ensure_indexes()
    now = _now_iso()
    domains_collection().update_one(
        {"domain_name": domain_name},
        {
            "$set": {
                "domain_name": domain_name,
                "status": "running",
                "total_pages": 0,
                "total_urls_crawled": 0,
                "crawled_pages": 0,
                "failed_pages": 0,
                "start_url": start_url,
                "updated_at": now,
                "last_crawled_at": now,
                "total_crawl_time": 0,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    doc = domains_collection().find_one({"domain_name": domain_name})
    if not doc:
        raise RuntimeError(f"failed to create domain record for {domain_name}")
    return str(doc["_id"])


def count_domain_pages(domain_id: str) -> int:
    """Total documents in pages for this domain (all crawls)."""
    return pages_collection().count_documents({"domain_id": _object_id(domain_id)})


def finish_domain_crawl(
    domain_id: str,
    status: str,
    *,
    crawled_pages: int,
    failed_pages: int,
    total_crawl_time: float,
) -> None:
    if status not in DOMAIN_STATUSES:
        raise ValueError(f"invalid status: {status}")
    now = _now_iso()
    total_pages = count_domain_pages(domain_id)
    total_urls_crawled = crawled_pages + failed_pages
    domains_collection().update_one(
        {"_id": _object_id(domain_id)},
        {
            "$set": {
                "status": status,
                "total_pages": total_pages,
                "total_urls_crawled": total_urls_crawled,
                "crawled_pages": crawled_pages,
                "failed_pages": failed_pages,
                "total_crawl_time": round(total_crawl_time, 2),
                "updated_at": now,
                "last_crawled_at": now,
            }
        },
    )


def increment_domain_failed_pages(domain_id: str, count: int = 1) -> None:
    now = _now_iso()
    domains_collection().update_one(
        {"_id": _object_id(domain_id)},
        {
            "$inc": {"failed_pages": count},
            "$set": {"updated_at": now, "last_crawled_at": now},
        },
    )


def save_page(domain_id: str, record: SeoPageRecord | dict[str, Any]) -> bool:
    """Upsert page by (domain_id, url); preserve created_at on updates."""
    try:
        if isinstance(record, SeoPageRecord):
            clean = record.to_mongo_dict()
        else:
            clean = {k: record[k] for k in record if k in PAGE_FIELDS}
        if "url" not in clean:
            raise ValueError("document missing url")

        now = _now_iso()
        clean["domain_id"] = _object_id(domain_id)
        set_fields = {k: v for k, v in clean.items() if k not in ("created_at", "domain_id")}
        set_fields["updated_at"] = now
        set_fields["is_duplicate"] = bool(clean.get("is_duplicate", False))
        set_fields.setdefault("error", None)

        pages_collection().update_one(
            {"domain_id": _object_id(domain_id), "url": clean["url"]},
            {"$set": set_fields, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        return True
    except (PyMongoError, ValueError) as exc:
        url = getattr(record, "url", None) if isinstance(record, SeoPageRecord) else record.get("url")
        logger.error("MongoDB save failed for %s: %s", url, exc)
        return False


def save_failed_page(domain_id: str, domain_name: str, url: str, error: str) -> bool:
    """Record a failed URL with reason."""
    try:
        norm = normalize_url(url)
        now = _now_iso()
        pages_collection().update_one(
            {"domain_id": _object_id(domain_id), "url": norm},
            {
                "$set": {
                    "domain": domain_name,
                    "normalized_url": norm,
                    "page_name": page_slug(norm),
                    "error": error,
                    "is_duplicate": False,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now, "url": norm},
            },
            upsert=True,
        )
        increment_domain_failed_pages(domain_id)
        return True
    except PyMongoError as exc:
        logger.error("MongoDB failed-page record for %s: %s", url, exc)
        return False


def find_page_by_url(domain_id: str, url: str) -> dict[str, Any] | None:
    return pages_collection().find_one(
        {"domain_id": _object_id(domain_id), "url": normalize_url(url)}
    )


def find_domain_by_name(domain_name: str) -> dict[str, Any] | None:
    return domains_collection().find_one({"domain_name": domain_name})
