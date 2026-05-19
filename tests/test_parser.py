"""Parser unit tests (pure functions)."""

from parser import extract_links, parse_seo


def test_parse_seo():
    html = "<html><head><title>T</title></head><body><h1>H</h1></body></html>"
    data = parse_seo(
        "https://example.com/a",
        "https://example.com/a",
        html,
        200,
        "html/example.com/page-1.html",
    )
    assert data["title"] == "T"
    assert data["h1"] == ["H"]
    assert data["page_name"] == "a"


def test_extract_links_excludes_subdomains():
    html = '<a href="/ok">OK</a><a href="https://blog.example.com/x">X</a>'
    links = extract_links(html, "https://example.com/", "example.com")
    assert links == ["https://example.com/ok"]
