"""SEO page model tests."""

from models import SeoPageRecord, build_seo_page_record


def test_build_seo_page_record():
    parsed = {
        "url": "https://example.com/about",
        "normalized_url": "https://example.com/about",
        "page_name": "about",
        "title": "About",
        "meta_description": "Desc",
        "canonical_url": "https://example.com/about",
        "h1": ["About us"],
        "h2": [],
        "h3": [],
        "h4": [],
        "http_status_code": 200,
        "html_file_path": "html/example.com/page-1.html",
    }
    record = build_seo_page_record(
        parsed, domain="example.com", fetch_method="playwright", retry_count=0
    )
    assert isinstance(record, SeoPageRecord)
    assert record.domain == "example.com"
    assert record.id
    assert record.to_mongo_dict()["url"] == parsed["url"]
