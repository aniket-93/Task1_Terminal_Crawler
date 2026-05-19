"""SEO page record model (in-memory schema before persistence)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from models.schema import ALLOWED_FIELDS
from utils.page_id import make_page_id


@dataclass
class SeoPageRecord:
    id: str
    domain: str
    url: str
    normalized_url: str
    page_name: str
    title: str | None
    meta_description: str | None
    canonical_url: str | None
    h1: list[str]
    h2: list[str]
    h3: list[str] = field(default_factory=list)
    h4: list[str] = field(default_factory=list)
    http_status_code: int = 200
    html_file_path: str = ""
    fetch_method: str = ""
    retry_count: int = 0

    def to_mongo_dict(self) -> dict[str, Any]:
        """Dict restricted to Mongo allowlist (no timestamps; repository adds those)."""
        return {k: v for k, v in asdict(self).items() if k in ALLOWED_FIELDS}


def build_seo_page_record(
    parsed: dict[str, Any],
    *,
    domain: str,
    fetch_method: str,
    retry_count: int,
) -> SeoPageRecord:
    """Build a page record from parser output plus crawl metadata."""
    normalized = parsed["normalized_url"]
    return SeoPageRecord(
        id=make_page_id(normalized),
        domain=domain,
        url=parsed["url"],
        normalized_url=normalized,
        page_name=parsed["page_name"],
        title=parsed.get("title"),
        meta_description=parsed.get("meta_description"),
        canonical_url=parsed.get("canonical_url"),
        h1=list(parsed.get("h1") or []),
        h2=list(parsed.get("h2") or []),
        h3=list(parsed.get("h3") or []),
        h4=list(parsed.get("h4") or []),
        http_status_code=int(parsed.get("http_status_code") or 200),
        html_file_path=parsed.get("html_file_path") or "",
        fetch_method=fetch_method,
        retry_count=retry_count,
    )
