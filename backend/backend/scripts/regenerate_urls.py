"""Regenerate wallpaper URLs using current storage config.

Run inside the backend container:
    python -m backend.scripts.regenerate_urls

This reads every Wallpaper row, extracts the object key from the stored URL,
and regenerates the URL via the active storage backend. This is useful after
enabling/disabling signed URLs or switching CDN domains.
"""
import os
import re
from urllib.parse import urlparse

from backend.database import SessionLocal
from backend.models import Wallpaper
from backend.storage import get_storage


def _extract_key_from_url(url: str, path_prefix: str) -> str | None:
    """Best-effort extraction of the storage-relative key from a stored URL.

    The key passed to storage.save() does NOT include path_prefix; path_prefix
    is added internally by the storage backend. Therefore we must strip it here.
    """
    if not url:
        return None
    from urllib.parse import unquote, urlparse
    # Strip query string and decode URL-encoded path separators
    url = unquote(url.split("?")[0])
    # Local URLs: /static/<path_prefix><key> -> drop /static/ and path_prefix
    if url.startswith("/static/"):
        path = url[len("/static/"):]
    else:
        path = urlparse(url).path.lstrip("/")
    prefix = path_prefix.strip("/")
    if prefix and path.startswith(prefix + "/"):
        return path[len(prefix) + 1:]
    # Fallbacks for legacy keys without path_prefix
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[-2] == "thumbnails":
        return f"{parts[-2]}/{parts[-1]}"
    if parts:
        return parts[-1]
    return None


def regenerate():
    db = SessionLocal()
    try:
        storage = get_storage(db)
        wallpapers = db.query(Wallpaper).all()
        print(f"Found {len(wallpapers)} wallpapers")
        updated = 0
        for wp in wallpapers:
            changed = False
            fields = [
                "original_url",
                "thumbnail_1080_url",
                "thumbnail_720_url",
                "thumbnail_small_url",
            ]
            for field in fields:
                old_url = getattr(wp, field)
                key = _extract_key_from_url(old_url, storage.path_prefix if hasattr(storage, "path_prefix") else "wallpapers/")
                if not key:
                    print(f"  ⚠️ Could not extract key for wallpaper {wp.id} field {field}: {old_url}")
                    continue
                try:
                    new_url = storage.url(key)
                except Exception as e:
                    print(f"  ⚠️ Failed to regenerate URL for wallpaper {wp.id} field {field} key={key}: {e}")
                    continue
                if new_url != old_url:
                    setattr(wp, field, new_url)
                    changed = True
            if changed:
                updated += 1
        db.commit()
        print(f"✅ Regenerated URLs for {updated} wallpapers")
    finally:
        db.close()


if __name__ == "__main__":
    regenerate()
