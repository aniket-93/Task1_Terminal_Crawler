"""Parser unit tests (pure functions)."""

from parser import extract_links, parse_seo


def test_parse_seo():
    html = "<html><head><title>T</title></head><body><h1>H</h1></body></html>"
    data = parse_seo(
        "https://example.com/a",
        "https://example.com/a",
        html,
        200,
        "html/example.com/a_index.html",
    )
    assert data["title"] == "T"
    assert data["h1"] == ["H"]
    assert data["page_name"] == "T"


def test_page_name_from_catalogue_style_url():
    html = (
        "<html><head><title>A Short History of Nearly Everything</title></head>"
        "<body><h1>Book</h1><h2>Details</h2></body></html>"
    )
    url = "https://books.toscrape.com/catalogue/a-short-history_103/index.html"
    data = parse_seo(url, url, html, 200, "html/books.toscrape.com/catalogue_a-short-history_103_index.html")
    assert data["page_name"] == "A Short History of Nearly Everything"
    assert data["h1"] == ["Book"]
    assert data["h2"] == ["Details"]
    assert data["canonical_url"] is None


def test_extract_links_excludes_subdomains():
    html = '<a href="/ok">OK</a><a href="https://blog.example.com/x">X</a>'
    links = extract_links(html, "https://example.com/", "example.com")
    assert links == ["https://example.com/ok"]
