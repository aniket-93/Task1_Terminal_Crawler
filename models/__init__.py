"""Database document models and schema."""

from models.schema import ALLOWED_FIELDS, INDEX_SPECS, domain_collection_name
from models.seo_page import SeoPageRecord, build_seo_page_record

__all__ = [
    "ALLOWED_FIELDS",
    "INDEX_SPECS",
    "SeoPageRecord",
    "build_seo_page_record",
    "domain_collection_name",
]
