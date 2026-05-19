"""URL normalization and domain matching."""

from urllib.parse import urljoin, urlparse, urlunparse

import validators

from utils.link_policy import should_follow_link
from utils.security import is_safe_crawl_target


def normalize_host(netloc: str) -> str:
    """Lowercase host without port; strip leading www."""
    host = netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def normalize_url(url: str) -> str:
    """
    Purpose: Canonical form for deduplication.
    Inputs: Raw URL.
    Outputs: Lower scheme/host, no fragment, trailing slash rule, query kept.
    """
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.params, parsed.query, "")
    )


def parse_user_input(value: str) -> tuple[str, str]:
    """
    Purpose: Validate terminal input into seed URL and allowed host.
    Inputs: User-entered domain or URL.
    Outputs: (seed_url, allowed_host).
    """
    value = value.strip()
    if not value:
        raise ValueError("Domain or URL is required")
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    if not validators.url(value):
        raise ValueError(f"Invalid URL: {value}")
    parsed = urlparse(value)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {value}")
    if parsed.username or parsed.password:
        raise ValueError("URLs with credentials are not allowed")
    if not is_safe_crawl_target(value):
        raise ValueError("Blocked or unsafe URL target")
    allowed = normalize_host(parsed.netloc)
    return normalize_url(value), allowed


def is_same_domain(url: str, allowed_host: str) -> bool:
    """
    Purpose: Strict domain match; subdomains excluded (www treated as same host).
    Inputs: URL and allowed host from seed.
    Outputs: True if crawl allowed.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    return normalize_host(parsed.netloc) == allowed_host


def resolve_link(base_url: str, href: str) -> str | None:
    """Resolve anchor href to normalized URL if crawlable."""
    if not isinstance(href, str):
        return None
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    absolute = normalize_url(urljoin(base_url, href))
    if not should_follow_link(absolute):
        return None
    return absolute


def page_slug(url: str) -> str:
    """Last path segment for page_name."""
    path = urlparse(url).path.strip("/")
    if not path:
        return "index"
    return path.split("/")[-1] or "index"
