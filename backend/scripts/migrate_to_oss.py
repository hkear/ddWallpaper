"""Migrate existing local wallpaper files to Aliyun OSS.

Usage (inside the backend container):
    python -m scripts.migrate_to_oss --dry-run
    python -m scripts.migrate_to_oss

Prerequisites:
- StorageConfig in DB is enabled with valid Aliyun OSS credentials
  (or OSS_* env vars are set).

What it does:
1. Scans wallpapers table for rows whose URLs are local /static/... paths.
2. Uploads each local file (original + thumbnails) to OSS via the storage layer.
3. Updates the DB rows with the new public URLs.
4. Idempotent: rows already using http(s) URLs are skipped.
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import Wallpaper
from backend.storage import get_storage
from backend.config import get_settings


def is_local_url(url: str) -> bool:
    return bool(url) and not url.startswith("http://") and not url.startswith("https://")


def migrate(dry_run: bool = False):
    settings = get_settings()
    db = SessionLocal()
    storage = get_storage(db)

    rows = db.query(Wallpaper).all()
    migrated = 0
    skipped = 0
    failed = 0

    for wp in rows:
        fields = {
            "original_url": wp.original_url,
            "thumbnail_1080_url": wp.thumbnail_1080_url,
            "thumbnail_720_url": wp.thumbnail_720_url,
            "thumbnail_small_url": wp.thumbnail_small_url,
        }
        updates = {}
        for field, url in fields.items():
            if not is_local_url(url):
                continue
            rel = url.lstrip("/")
            if rel.startswith("static/"):
                rel = rel[len("static/"):]
            local_path = os.path.join(settings.UPLOAD_DIR, rel)
            if not os.path.exists(local_path):
                print(f"⚠️  wp#{wp.id} {field}: local file missing {local_path}")
                failed += 1
                continue
            if dry_run:
                print(f"[dry-run] wp#{wp.id} {field}: {url} -> OSS key {rel}")
                updates[field] = f"<dry-run>/{rel}"
                continue
            try:
                new_url = storage.save(local_path, rel)
                updates[field] = new_url
                print(f"✅ wp#{wp.id} {field}: -> {new_url}")
            except Exception as e:
                print(f"❌ wp#{wp.id} {field}: upload failed: {e}")
                failed += 1

        if updates and not dry_run:
            for field, new_url in updates.items():
                setattr(wp, field, new_url)
            db.commit()
            migrated += 1
        elif updates and dry_run:
            migrated += 1
        else:
            skipped += 1

    db.close()
    print(f"\nDone. migrated={migrated} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)
