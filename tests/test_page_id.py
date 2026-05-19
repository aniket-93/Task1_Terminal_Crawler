"""Page id stability tests."""

from utils.page_id import make_page_id


def test_page_id_stable_for_same_url():
    url = "https://example.com/about"
    assert make_page_id(url) == make_page_id(url)


def test_page_id_differs_for_different_urls():
    assert make_page_id("https://example.com/a") != make_page_id("https://example.com/b")
