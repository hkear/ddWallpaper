import os
import math
import uuid
import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.database import get_db
from backend.models import Wallpaper, Category, User, Favorite, Like, WallpaperStatus, DeviceType
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

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_upload_dir():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def _build_urls(filename: str) -> dict:
    base = "/static"
    f = filename
    return {
        "original_url": f"{base}/{f}",
        "thumbnail_1080_url": f"{base}/{f}",
        "thumbnail_720_url": f"{base}/{f}",
        "thumbnail_small_url": f"{base}/{f}",
    }


def _wallpaper_to_out(wp: Wallpaper) -> WallpaperOut:
    return WallpaperOut(
        id=wp.id,
        title=wp.title,
        description=wp.description,
        device_type=wp.device_type,
        category_id=wp.category_id,
        tags=wp.tags or [],
        resolution=wp.resolution,
        file_size=wp.file_size,
        original_url=wp.original_url,
        thumbnail_1080_url=wp.thumbnail_1080_url,
        thumbnail_720_url=wp.thumbnail_720_url,
        thumbnail_small_url=wp.thumbnail_small_url,
        format=wp.format,
        width=wp.width,
        height=wp.height,
        downloads=wp.downloads,
        likes=wp.likes,
        status=wp.status,
        author_id=wp.author_id,
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
    device_type: DeviceType,
    category_id: int,
    tags: str,
    description: str | None,
    author_id: int,
    status: WallpaperStatus,
    db: Session,
) -> Wallpaper:
    """Shared helper to persist an uploaded wallpaper and generate thumbnails."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=400, detail="分类不存在")

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

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    width, height = orig_width, orig_height

    wp = Wallpaper(
        title=title,
        device_type=device_type,
        category_id=category_id,
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
        q = q.filter(Wallpaper.device_type == device_type)
    if category:
        q = q.filter(Wallpaper.category_id == category)
    if tag:
        q = q.filter(Wallpaper.tags.contains(tag))
    if search:
        q = q.filter(or_(
            Wallpaper.title.ilike(f"%{search}%"),
            Wallpaper.description.ilike(f"%{search}%"),
        ))

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
        items=[_wallpaper_to_out(w) for w in items],
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
    return _wallpaper_to_out(wp)


@router.post("/", response_model=WallpaperOut)
def upload_wallpaper(
    title: str = Form(...),
    device_type: DeviceType = Form(DeviceType.PORTRAIT),
    category_id: int = Form(...),
    tags: str = Form(""),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    status = WallpaperStatus.APPROVED if user.is_admin else WallpaperStatus.PENDING
    wp = _save_wallpaper_upload(file, title, device_type, category_id, tags, description, user.id, status, db)

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

    return _wallpaper_to_out(wp)


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

    # Admin can delete any wallpaper
    if user.is_admin:
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

    _delete_wallpaper_files(db, wp)
    db.delete(wp)
    db.commit()
    return {"ok": True}
