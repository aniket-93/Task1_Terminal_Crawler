"""Block unsafe crawl targets."""

import ipaddress
import re
from urllib.parse import urlparse

_BLOCKED = frozenset({"localhost", "localhost.localdomain", "metadata.google.internal"})


def is_safe_crawl_target(url: str) -> bool:
    """
    Purpose: SSRF guard for crawl targets.
    Inputs: URL string.
    Outputs: True if allowed to fetch.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False
    h = host.lower().strip(".")
    if h in _BLOCKED or h.endswith(".localhost") or h.endswith(".local"):
        return False
    try:
        addr = ipaddress.ip_address(host)
        return not (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
        )
    except ValueError:
        if re.fullmatch(r"[\d.]+", host):
            try:
                addr = ipaddress.ip_address(host)
                return not (addr.is_private or addr.is_loopback or addr.is_link_local)
            except ValueError:
                return False
    return True
