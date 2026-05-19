"""Stable page identifiers derived from normalized URL."""

import uuid


def make_page_id(normalized_url: str) -> str:
    """Same URL always yields the same id (survives Mongo upserts and re-crawls)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, normalized_url))
