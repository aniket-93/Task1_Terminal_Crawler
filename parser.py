"""Pure HTML parsing — no I/O."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from utils.url_utils import is_same_domain, page_slug, resolve_link


def page_name_from_title(title: str | None, url: str) -> str:
    """Human-readable page name: document title, else URL path slug."""
    if title and title.strip():
        return " ".join(title.split())[:500]
    return page_slug(url)


def parse_seo(url: str, normalized_url: str, html: str, status_code: int, html_path: str) -> dict:
    """
    Purpose: Extract SEO fields from HTML.
    Inputs: URLs, HTML body, HTTP status, saved file path.
    Outputs: Dict of SEO fields (no side effects).
    """
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    meta = _meta(soup, "name", "description") or _meta(soup, "property", "og:description")
    canonical = None
    link = soup.find("link", rel=lambda v: v and "canonical" in str(v).lower())
    if link and isinstance(link, Tag) and link.get("href"):
        canonical = urljoin(url, str(link.get("href")).strip())

    return {
        "url": url,
        "normalized_url": normalized_url,
        "page_name": page_name_from_title(title, url),
        "title": title,
        "meta_description": meta,
        "canonical_url": canonical,
        "h1": _tags(soup, "h1"),
        "h2": _tags(soup, "h2"),
        "h3": _tags(soup, "h3"),
        "h4": _tags(soup, "h4"),
        "http_status_code": status_code,
        "html_file_path": html_path,
    }


def extract_links(html: str, base_url: str, allowed_host: str) -> list[str]:
    """
    Purpose: Find internal links for BFS enqueue.
    Inputs: HTML, base URL, allowed host.
    Outputs: List of normalized same-domain URLs.
    """
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        resolved = resolve_link(base_url, href) if href else None
        if not resolved or not is_same_domain(resolved, allowed_host):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(resolved)
    return out


def _meta(soup: BeautifulSoup, attr: str, val: str) -> str | None:
    tag = soup.find("meta", attrs={attr: val})
    if tag and isinstance(tag, Tag) and tag.get("content"):
        return str(tag.get("content")).strip()
    return None


def _tags(soup: BeautifulSoup, name: str) -> list[str]:
    return [t for t in (x.get_text(strip=True) for x in soup.find_all(name)) if t]
