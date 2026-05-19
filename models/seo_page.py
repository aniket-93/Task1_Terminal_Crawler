"""SEO page record model (in-memory before persistence)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from models.schema import PAGE_FIELDS


@dataclass
class SeoPageRecord:
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
    error: str | None = None
    is_duplicate: bool = False

    def to_mongo_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k in PAGE_FIELDS}


def build_seo_page_record(
    parsed: dict[str, Any],
    *,
    domain: str,
    fetch_method: str,
    retry_count: int,
    error: str | None = None,
    is_duplicate: bool = False,
) -> SeoPageRecord:
    return SeoPageRecord(
        domain=domain,
        url=parsed["url"],
        normalized_url=parsed["normalized_url"],
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
        error=error,
        is_duplicate=is_duplicate,
    )
