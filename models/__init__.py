"""Database document models and schema."""

from models.schema import (
    DOMAIN_FIELDS,
    DOMAINS_COLLECTION,
    DOMAIN_STATUSES,
    PAGE_FIELDS,
    PAGES_COLLECTION,
)
from models.seo_page import SeoPageRecord, build_seo_page_record

__all__ = [
    "DOMAIN_FIELDS",
    "DOMAIN_STATUSES",
    "DOMAINS_COLLECTION",
    "PAGE_FIELDS",
    "PAGES_COLLECTION",
    "SeoPageRecord",
    "build_seo_page_record",
]
