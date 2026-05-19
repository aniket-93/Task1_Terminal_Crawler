"""HTML path naming from URL."""

from storage.file_storage import (
    html_filename_for_url,
    path_slug_from_url,
    relative_html_path,
)


def test_root_index_html():
    assert html_filename_for_url("https://www.ebrandz.in/") == "index.html"
    assert relative_html_path("ebrandz.in", "https://www.ebrandz.in/") == (
        "html/ebrandz.in/index.html"
    )


def test_social_media_path():
    url = "https://www.ebrandz.in/social-media/"
    assert path_slug_from_url(url) == "social-media"
    assert html_filename_for_url(url) == "social-media_index.html"
    assert relative_html_path("ebrandz.in", url) == "html/ebrandz.in/social-media_index.html"


def test_nested_path():
    url = "https://www.ebrandz.in/careers/seo-executive"
    assert html_filename_for_url(url) == "careers_seo-executive_index.html"
