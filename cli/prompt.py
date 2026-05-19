"""Terminal input for domain / URL."""

from utils.url_utils import parse_user_input


def prompt_domain() -> tuple[str, str]:
    """Read and validate crawl target from stdin. Returns (seed_url, allowed_host)."""
    raw = input("Enter domain or URL to crawl (e.g. example.com): ").strip()
    return parse_user_input(raw)
