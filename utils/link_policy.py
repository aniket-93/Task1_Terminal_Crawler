"""Skip non-HTML resource links."""

from urllib.parse import urlparse

SKIP_SCHEMES = {"mailto", "tel", "javascript", "data", "blob"}
SKIP_EXTENSIONS = {
    ".pdf", ".zip", ".rar", ".7z", ".gz", ".tar",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".mp4", ".mp3", ".avi", ".mov",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".css", ".js", ".json", ".xml", ".rss",
}


def should_follow_link(url: str) -> bool:
    """
    Purpose: Decide if a URL should be enqueued for crawling.
    Inputs: Absolute normalized URL.
    Outputs: True for likely HTML pages.
    """
    parsed = urlparse(url)
    if parsed.scheme in SKIP_SCHEMES or parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc:
        return False
    path = (parsed.path or "").lower()
    return not any(path.endswith(ext) for ext in SKIP_EXTENSIONS)
