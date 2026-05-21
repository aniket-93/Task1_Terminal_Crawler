"""Application configuration (env overrides supported)."""

import os

MAX_PAGES = int(os.getenv("MAX_PAGES", "0"))  # optional cap if you pass max_pages manually; 0 = unlimited
MAX_PAGES_WHOLE_SITE = int(
    os.getenv("MAX_PAGES_WHOLE_SITE", "0")
)  # default terminal crawl limit; 0 = crawl all same-domain pages
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "10"))
REQUEST_DELAY_MS = int(os.getenv("REQUEST_DELAY_MS", "300"))
REQUEST_TIMEOUT_SEC = int(os.getenv("REQUEST_TIMEOUT_SEC", "30"))
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", str(5 * 1024 * 1024)))
MIN_HTML_BYTES = int(os.getenv("MIN_HTML_BYTES", "100"))

# Crawlee treats 4xx as errors by default; these are passed through to our handler instead.
# Comma-separated HTTP codes (e.g. dead links returning 404 on the target site).
IGNORE_HTTP_STATUS_CODES: tuple[int, ...] = tuple(
    int(code.strip())
    for code in os.getenv("IGNORE_HTTP_STATUS_CODES", "404,410").split(",")
    if code.strip()
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "seo_crawler")

HTML_DIR = os.getenv("HTML_DIR", "html")
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

USER_AGENT = os.getenv(
    "USER_AGENT",
    "SEO-Crawler-POC/1.0 (+local; respectful bot)",
)
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# Purge Crawlee storage between runs (avoids stale queue on re-runs)
CRAWLEE_PURGE_ON_START = os.getenv("CRAWLEE_PURGE_ON_START", "true").lower() == "true"
