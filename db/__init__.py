"""Database access layer."""

from db.repository import find_page_by_url, get_collection, ping, save_page

__all__ = ["find_page_by_url", "get_collection", "ping", "save_page"]
