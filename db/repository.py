"""MongoDB insert and query logic (no document models here)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from config import DB_NAME, MONGO_URI
from models.schema import ALLOWED_FIELDS, INDEX_SPECS, domain_collection_name
from models.seo_page import SeoPageRecord

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_indexed_collections: set[str] = set()


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_collection(domain: str) -> Collection:
    name = domain_collection_name(domain)
    col = get_client()[DB_NAME][name]
    if name not in _indexed_collections:
        for field, opts in INDEX_SPECS:
            col.create_index(field, **opts)
        _indexed_collections.add(name)
    return col


def ping() -> None:
    get_client().admin.command("ping")


def save_page(domain: str, record: SeoPageRecord | dict[str, Any]) -> bool:
    """Upsert page by url; preserve created_at on updates."""
    try:
        if isinstance(record, SeoPageRecord):
            clean = record.to_mongo_dict()
        else:
            clean = {k: record[k] for k in record if k in ALLOWED_FIELDS}
        if "url" not in clean:
            raise ValueError("document missing url")
        now = datetime.now(timezone.utc).isoformat()
        set_fields = {k: v for k, v in clean.items() if k != "created_at"}
        set_fields["updated_at"] = now
        col = get_collection(domain)
        col.update_one(
            {"url": clean["url"]},
            {"$set": set_fields, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        return True
    except (PyMongoError, ValueError) as exc:
        url = getattr(record, "url", None) if isinstance(record, SeoPageRecord) else record.get("url")
        logger.error("MongoDB save failed for %s: %s", url, exc)
        return False


def find_page_by_url(domain: str, url: str) -> dict[str, Any] | None:
    """Return stored page document for a URL, or None."""
    doc = get_collection(domain).find_one({"url": url})
    return doc
