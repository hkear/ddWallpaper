import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Wallpaper, Favorite, WallpaperStatus
from backend.schemas import WallpaperOut, WallpaperList
from backend.auth import get_current_user
from backend.routers.wallpapers import _wallpaper_to_out

router = APIRouter(prefix="/users/me", tags=["用户"])


@router.get("/favorites", response_model=WallpaperList)
def list_favorites(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from backend.models import User
    user: User = user
    fav_q = (
        db.query(Wallpaper)
        .join(Favorite, Favorite.wallpaper_id == Wallpaper.id)
        .filter(
            Favorite.user_id == user.id,
            Wallpaper.status == WallpaperStatus.APPROVED,
        )
        .order_by(Favorite.created_at.desc())
    )
    total = fav_q.count()
    items = fav_q.offset((page - 1) * size).limit(size).all()
    return WallpaperList(
        items=[_wallpaper_to_out(w, db) for w in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("/favorites/{wallpaper_id}")
def toggle_favorite(
    wallpaper_id: int,
    user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from backend.models import User
    user: User = user
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="壁纸不存在")

    existing = db.query(Favorite).filter(
        Favorite.user_id == user.id, Favorite.wallpaper_id == wallpaper_id
    ).first()

    if existing:
        db.delete(existing)
        favorited = False
    else:
        db.add(Favorite(user_id=user.id, wallpaper_id=wallpaper_id))
        favorited = True
    db.commit()
    return {"favorited": favorited}


@router.get("/submissions", response_model=WallpaperList)
def list_submissions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from backend.models import User
    user: User = user
    q = (
        db.query(Wallpaper)
        .filter(Wallpaper.author_id == user.id)
        .order_by(Wallpaper.created_at.desc())
    )
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return WallpaperList(
        items=[_wallpaper_to_out(w, db) for w in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )
