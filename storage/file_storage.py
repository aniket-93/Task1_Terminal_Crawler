"""Save crawled HTML under html/{domain}/{path-slug}_index.html."""

import os
import re
from urllib.parse import urlparse

from config import HTML_DIR
from utils.url_utils import normalize_url

_MAX_SLUG_LEN = 180


def domain_html_dir(domain: str) -> str:
    """Return html/{domain}/ path (e.g. html/ebrandz.in/)."""
    return os.path.join(HTML_DIR, domain)


def path_slug_from_url(url: str) -> str:
    """
    Build file stem from URL path.
    / -> index
    /social-media -> social-media
    /careers/seo-executive -> careers_seo-executive
    """
    parsed = urlparse(normalize_url(url))
    path = (parsed.path or "/").strip("/")
    if not path:
        return "index"
    slug = path.replace("/", "_")
    slug = re.sub(r"[^a-zA-Z0-9._-]", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("._-")
    return slug[:_MAX_SLUG_LEN] or "index"


def html_filename_for_url(url: str) -> str:
    """e.g. social-media_index.html or index.html for site root."""
    slug = path_slug_from_url(url)
    if slug == "index":
        return "index.html"
    return f"{slug}_index.html"


def html_path_for_save(domain: str, url: str) -> str:
    """Absolute path for writing HTML; ensures domain dir exists."""
    base = domain_html_dir(domain)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, html_filename_for_url(url))


def relative_html_path(domain: str, url: str) -> str:
    """Forward-slash path stored in MongoDB (html/ebrandz.in/social-media_index.html)."""
    filename = html_filename_for_url(url)
    return os.path.join(HTML_DIR, domain, filename).replace(os.sep, "/")


def save_html(path: str, html: str) -> None:
    """Write raw HTML; raises OSError on failure."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def crawl_summary_html_path(domain: str) -> str:
    """Run-level crawl report as HTML (no JSON on disk)."""
    return os.path.join(domain_html_dir(domain), "crawl_summary.html")
