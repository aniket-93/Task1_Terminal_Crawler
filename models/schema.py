"""MongoDB collection names, field allowlists, and indexes."""

DOMAINS_COLLECTION = "domains"
PAGES_COLLECTION = "pages"

DOMAIN_STATUSES = frozenset({"queued", "running", "completed", "failed"})

DOMAIN_FIELDS = frozenset(
    {
        "domain_name",
        "status",
        "total_pages",
        "total_urls_crawled",
        "crawled_pages",
        "failed_pages",
        "start_url",
        "created_at",
        "updated_at",
        "last_crawled_at",
        "total_crawl_time",
    }
)

PAGE_FIELDS = frozenset(
    {
        "domain_id",
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
        "error",
        "is_duplicate",
        "created_at",
        "updated_at",
    }
)

DOMAIN_INDEX_SPECS = (
    ("domain_name", {"unique": True}),
    ("status", {}),
)

PAGE_INDEX_SPECS = (
    (("domain_id", "url"), {"unique": True}),
    ("domain_id", {}),
    ("normalized_url", {}),
)
