import os
import math
import uuid
import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, String
from backend.database import get_db
from backend.models import Wallpaper, Category, User, Favorite, Like, WallpaperStatus, DeviceType, WallpaperDeviceType, WallpaperCategory, SiteConfig
from backend.schemas import WallpaperOut, WallpaperList, WallpaperUpload, LikeOut, SubmissionList
from PIL import Image as PILImage
from backend.auth import get_current_user_optional, get_current_user
from backend.config import get_settings
from backend import webhook
from backend.storage import get_storage

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wallpapers", tags=["壁纸"])

ALLOWED_EXT = {"jpg", "jpeg", "png", "webp", "gif"}

MAX_DESCRIPTION_LENGTH = 30
MAX_TAGS_LENGTH = 20

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _ensure_upload_dir():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def _get_site_config_upload_enabled(db: Session) -> bool:
    cfg = db.query(SiteConfig).filter(SiteConfig.id == 1).first()
    if not cfg:
        cfg = SiteConfig(id=1, upload_enabled=True)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg.upload_enabled


def _build_urls(filename: str) -> dict:
    base = "/static"
    f = filename
    return {
        "original_url": f"{base}/{f}",
        "thumbnail_1080_url": f"{base}/{f}",
        "thumbnail_720_url": f"{base}/{f}",
        "thumbnail_small_url": f"{base}/{f}",
    }


def _normalize_tags(tags: str) -> list[str]:
    raw = tags.replace("，", ",").replace(",", ",")
    return [t.strip() for t in raw.split(",") if t.strip()]


def _refresh_signed_url(url: str, storage) -> str:
    """Refresh the OSS signed URL of a stored image URL.

    URLs persisted in DB are signed with a 7-day validity; once expired the
    thumbnails / previews return 403. Re-extract the object key and re-sign it
    so the returned URL is always fresh. Falls back to the stored URL when the
    URL is not remote or the key cannot be extracted.
    """
    if not url:
        return url
    if not (url.startswith("http://") or url.startswith("https://")):
        return url
    try:
        key = _extract_key_from_url(url, getattr(storage, "path_prefix", "wallpapers/"))
        if key:
            fresh = storage.url(key)
            if fresh:
                return fresh
    except Exception as e:
        logger.warning(f"Failed to refresh signed URL {url[:80]}: {e}")
    return url


def _wallpaper_to_out(wp: Wallpaper, db: Session = None) -> WallpaperOut:
    category_ids = [wc.category_id for wc in wp.categories]
    category_names = [wc.category.name for wc in wp.categories if wc.category]

    if db is not None:
        storage = get_storage(db)
        original_url = _refresh_signed_url(wp.original_url, storage)
        thumb_1080 = _refresh_signed_url(wp.thumbnail_1080_url, storage)
        thumb_720 = _refresh_signed_url(wp.thumbnail_720_url, storage)
        thumb_small = _refresh_signed_url(wp.thumbnail_small_url, storage)
    else:
        original_url = wp.original_url
        thumb_1080 = wp.thumbnail_1080_url
        thumb_720 = wp.thumbnail_720_url
        thumb_small = wp.thumbnail_small_url

    return WallpaperOut(
        id=wp.id,
        title=wp.title,
        description=wp.description,
        device_types=[dt.device_type for dt in wp.device_types],
        category_id=category_ids[0] if category_ids else wp.category_id,
        category_ids=category_ids,
        category_names=category_names,
        tags=wp.tags or [],
        resolution=wp.resolution,
        file_size=wp.file_size,
        original_url=original_url,
        thumbnail_1080_url=thumb_1080,
        thumbnail_720_url=thumb_720,
        thumbnail_small_url=thumb_small,
        format=wp.format,
        width=wp.width,
        height=wp.height,
        downloads=wp.downloads,
        likes=wp.likes,
        status=wp.status,
        author_id=wp.author_id,
        author_name=wp.author.username if wp.author else None,
        created_at=wp.created_at,
    )

THUMBNAIL_SIZES = {
    "small": 300,
    "720": 720,
    "1080": 1080,
}


def _save_wallpaper_upload(
    file: UploadFile,
    title: str,
    device_types: list[DeviceType],
    category_ids: list[int],
    tags: str,
    description: str | None,
    author_id: int,
    status: WallpaperStatus,
    db: Session,
) -> Wallpaper:
    """Shared helper to persist an uploaded wallpaper and generate thumbnails."""
    category_ids = [cid for cid in category_ids if cid]
    if not category_ids:
        raise HTTPException(status_code=400, detail="请选择至少一个分类")
    cats = db.query(Category).filter(Category.id.in_(category_ids)).all()
    if len(cats) != len(category_ids):
        raise HTTPException(status_code=400, detail="分类不存在")

    # Text validation
    if description and len(description) > MAX_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail=f"描述不能超过 {MAX_DESCRIPTION_LENGTH} 字")
    tag_list = _normalize_tags(tags)
    tags_str = ",".join(tag_list)
    if len(tags_str) > MAX_TAGS_LENGTH:
        raise HTTPException(status_code=400, detail=f"标签总长度不能超过 {MAX_TAGS_LENGTH} 字")

    _ensure_upload_dir()
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    base_name = uuid.uuid4().hex
    safe_name = f"{base_name}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    content = file.file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件超过20MB限制")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="空文件")

    # Save original
    with open(file_path, "wb") as f:
        f.write(content)

    # Open image and generate thumbnails
    try:
        pil_img = PILImage.open(file_path)
        pil_img = pil_img.convert("RGB") if pil_img.mode in ("RGBA", "P", "LA") else pil_img
        orig_width, orig_height = pil_img.size
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"无法读取图片: {e}")

    thumb_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_paths = {}
    for key, max_size in THUMBNAIL_SIZES.items():
        thumb_name = f"{base_name}_{key}.{ext}"
        thumb_path = os.path.join(thumb_dir, thumb_name)
        img_copy = pil_img.copy()
        img_copy.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)
        if ext == "png":
            img_copy.save(thumb_path, "PNG", optimize=True)
        else:
            img_copy.save(thumb_path, "JPEG", quality=85, optimize=True)
        thumb_paths[key] = (thumb_name, thumb_path)

    # Persist via storage backend (local or OSS)
    storage = get_storage(db)
    try:
        original_url = storage.save(file_path, safe_name)
        thumb_urls = {}
        for key, (thumb_name, thumb_path) in thumb_paths.items():
            thumb_urls[key] = storage.save(thumb_path, f"thumbnails/{thumb_name}")
    except Exception as e:
        for _, thumb_path in thumb_paths.values():
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"文件存储失败: {e}")

    width, height = orig_width, orig_height

    wp = Wallpaper(
        title=title,
        category_id=category_ids[0],
        tags=tag_list,
        description=description,
        original_url=original_url,
        thumbnail_1080_url=thumb_urls.get("1080", original_url),
        thumbnail_720_url=thumb_urls.get("720", original_url),
        thumbnail_small_url=thumb_urls.get("small", original_url),
        file_size=len(content),
        format=ext,
        width=width,
        height=height,
        resolution=f"{width}x{height}" if width and height else None,
        author_id=author_id,
        status=status,
    )
    db.add(wp)
    db.commit()
    db.refresh(wp)
    for cid in category_ids:
        db.add(WallpaperCategory(wallpaper_id=wp.id, category_id=cid))
    for dt in device_types:
        db.add(WallpaperDeviceType(wallpaper_id=wp.id, device_type=dt))
    db.commit()
    db.refresh(wp)
    return wp


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=WallpaperList)
def list_wallpapers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: int = Query(None),
    device_type: DeviceType = Query(None),
    tag: str = Query(None),
    sort: str = Query("newest"),  # newest / downloads / likes
    search: str = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user_optional),
):
    q = db.query(Wallpaper).filter(Wallpaper.status == WallpaperStatus.APPROVED)

    if device_type:
        q = q.join(Wallpaper.device_types).filter(WallpaperDeviceType.device_type == device_type)
    if category:
        q = q.join(Wallpaper.categories).filter(WallpaperCategory.category_id == category)
    if tag:
        q = q.filter(Wallpaper.tags.contains(tag))
    if search:
        q = q.outerjoin(Wallpaper.categories).outerjoin(Category).filter(or_(
            Wallpaper.title.ilike(f"%{search}%"),
            Wallpaper.description.ilike(f"%{search}%"),
            Wallpaper.tags.cast(String).ilike(f"%{search}%"),
            Category.name.ilike(f"%{search}%"),
        )).distinct()

    if sort == "downloads":
        q = q.order_by(Wallpaper.downloads.desc())
    elif sort == "likes":
        q = q.order_by(Wallpaper.likes.desc())
    else:
        q = q.order_by(Wallpaper.created_at.desc())

    total = q.count()
    pages = math.ceil(total / size) if total > 0 else 1
    items = q.offset((page - 1) * size).limit(size).all()

    return WallpaperList(
        items=[_wallpaper_to_out(w, db) for w in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{wallpaper_id}", response_model=WallpaperOut)
def get_wallpaper(
    wallpaper_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user_optional),
):
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="壁纸不存在")
    return _wallpaper_to_out(wp, db)


@router.post("/", response_model=WallpaperOut)
def upload_wallpaper(
    title: str = Form(...),
    device_types: str = Form("portrait"),
    device_type: Optional[str] = Form(None),
    category_id: int = Form(None),
    category_ids: str = Form(""),
    tags: str = Form(""),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _get_site_config_upload_enabled(db):
        raise HTTPException(status_code=403, detail="上传功能已关闭")

    raw = device_types
    if device_type and device_type != raw:
        raw = device_type
    dt_list = [DeviceType(d.strip()) for d in raw.split(",") if d.strip()]

    cid_list: list[int] = []
    if category_ids:
        cid_list = [int(c.strip()) for c in category_ids.split(",") if c.strip().isdigit()]
    if not cid_list and category_id:
        cid_list = [category_id]

    status = WallpaperStatus.APPROVED if user.is_admin else WallpaperStatus.PENDING
    wp = _save_wallpaper_upload(file, title, dt_list, cid_list, tags, description, user.id, status, db)

    # Notify admins about the new pending submission
    if status == WallpaperStatus.PENDING:
        webhook.send_webhook_async(
            db,
            "wallpaper_uploaded",
            {
                "id": wp.id,
                "title": wp.title,
                "username": user.username or f"user_{user.id}",
            },
        )

    return _wallpaper_to_out(wp, db)


@router.post("/{wallpaper_id}/like", response_model=LikeOut)
def toggle_like(
    wallpaper_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="壁纸不存在")

    existing = db.query(Like).filter(
        Like.wallpaper_id == wallpaper_id, Like.user_id == user.id
    ).first()

    if existing:
        db.delete(existing)
        wp.likes = max(0, wp.likes - 1)
        liked = False
    else:
        db.add(Like(wallpaper_id=wallpaper_id, user_id=user.id))
        wp.likes += 1
        liked = True

    db.commit()
    return LikeOut(likes=wp.likes, liked=liked)


def _mime_type_for_ext(ext: str) -> str:
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }.get(ext.lower(), "application/octet-stream")


@router.get("/{wallpaper_id}/download")
def download_wallpaper(
    wallpaper_id: int,
    db: Session = Depends(get_db),
    _: Optional[User] = Depends(get_current_user_optional),
):
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="壁纸不存在")
    if wp.status != WallpaperStatus.APPROVED:
        raise HTTPException(status_code=403, detail="该壁纸暂不可下载")

    # Increment download count
    wp.downloads += 1
    db.commit()

    # Remote storage (OSS / CDN): redirect to a freshly generated URL so that
    # toggling signed_url or CDN domain takes effect immediately.
    if wp.original_url.startswith("http://") or wp.original_url.startswith("https://"):
        storage = get_storage(db)
        key = _extract_key_from_url(wp.original_url, getattr(storage, "path_prefix", "wallpapers/"))
        if key:
            try:
                return RedirectResponse(url=storage.url(key), status_code=302)
            except Exception as e:
                logger.warning(f"Failed to regenerate URL for wallpaper {wallpaper_id}: {e}")
        # Fallback to stored URL if regeneration fails
        return RedirectResponse(url=wp.original_url, status_code=302)

    file_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(wp.original_url.lstrip("/")))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(file_path, media_type=_mime_type_for_ext(wp.format))


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


PENDING_DELETE_WINDOW_HOURS = 24


def cleanup_stale_pending(db: Session) -> int:
    """Delete pending wallpapers older than the allowed window."""
    deadline = datetime.now(timezone.utc) - timedelta(hours=PENDING_DELETE_WINDOW_HOURS)
    q = db.query(Wallpaper).filter(
        Wallpaper.status == WallpaperStatus.PENDING,
        Wallpaper.created_at < deadline.replace(tzinfo=None),
    )
    count = q.count()
    if count:
        q.delete(synchronize_session=False)
        db.commit()
    return count


def _delete_wallpaper_files(db: Session, wp: Wallpaper):
    """Best-effort deletion of the wallpaper's files from the storage backend."""
    storage = get_storage(db)
    for url in (wp.original_url, wp.thumbnail_1080_url, wp.thumbnail_720_url, wp.thumbnail_small_url):
        if not url:
            continue
        if url.startswith("http://") or url.startswith("https://"):
            key = url.split("/", 3)[-1] if "/" in url[8:] else url
            prefix = getattr(storage, "path_prefix", None)
            if prefix and key.startswith(prefix):
                key = key[len(prefix):]
            try:
                storage.delete(key)
            except Exception:
                pass
        else:
            key = url.lstrip("/")
            if key.startswith("static/"):
                key = key[len("static/"):]
            try:
                storage.delete(key)
            except Exception:
                pass


@router.delete("/{wallpaper_id}")
def delete_wallpaper(
    wallpaper_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="壁纸不存在")

    def _cleanup_relations(wid: int):
        """Delete related favorites and likes before deleting wallpaper (FK constraints)."""
        from backend.models import Favorite, Like
        db.query(Favorite).filter(Favorite.wallpaper_id == wid).delete(synchronize_session=False)
        db.query(Like).filter(Like.wallpaper_id == wid).delete(synchronize_session=False)

    # Admin can delete any wallpaper
    if user.is_admin:
        _cleanup_relations(wallpaper_id)
        _delete_wallpaper_files(db, wp)
        db.delete(wp)
        db.commit()
        return {"ok": True}

    # Non-admin can only delete their own pending wallpapers within 24h
    if wp.author_id != user.id:
        raise HTTPException(status_code=403, detail="无权删除")
    if wp.status != WallpaperStatus.PENDING:
        raise HTTPException(status_code=403, detail="已通过审核的壁纸不能删除")

    deadline = datetime.now(timezone.utc) - timedelta(hours=PENDING_DELETE_WINDOW_HOURS)
    if wp.created_at and wp.created_at.replace(tzinfo=timezone.utc) < deadline:
        raise HTTPException(status_code=403, detail="审核超时，已不可手动删除")

    _cleanup_relations(wallpaper_id)
    _delete_wallpaper_files(db, wp)
    db.delete(wp)
    db.commit()
    return {"ok": True}
