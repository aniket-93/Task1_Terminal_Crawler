"""MongoDB schema: field allowlist, collection naming, indexes."""

import re

# Fields persisted for each crawled page (see models.seo_page.SeoPageRecord).
ALLOWED_FIELDS = frozenset(
    {
        "id",
        "domain",
        "url",
        "normalized_url",
        "page_name",
        "title",
        "meta_description",
        "canonical_url",
        "h1",
        "h2",
        "h3",
        "h4",
        "http_status_code",
        "html_file_path",
        "fetch_method",
        "retry_count",
        "created_at",
        "updated_at",
    }
)

INDEX_SPECS = (
    ("url", {"unique": True}),
    ("normalized_url", {}),
    ("id", {"unique": True}),
)


def domain_collection_name(domain: str) -> str:
    """One collection per domain: pages_example_com."""
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", domain.lower())
    return f"pages_{safe}"
