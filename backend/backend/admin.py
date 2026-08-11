from typing import List, Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import (
    Wallpaper, WallpaperStatus, User, DeviceType, WebhookConfig, Category, AuthConfig,
    StorageConfig, SmtpConfig, SmsConfig, Feedback, WallpaperDeviceType, DebugConfig, DebugLog,
    WallpaperCategory,
)
from backend.schemas import (
    WallpaperOut,
    WallpaperList,
    ApproveRequest,
    WallpaperStatusChange,
    UserOut,
    UserAdminUpdate,
    ResetPassword,
    WebhookConfigOut,
    WebhookConfigUpdate,
    CategoryOut,
    CategoriesList,
    CategoryCreate,
    CategoryUpdate,
    AuthConfigOut,
    AuthConfigUpdate,
    StorageConfigOut,
    StorageConfigUpdate,
    SmtpConfigOut,
    SmtpConfigUpdate,
    SmsConfigOut,
    SmsConfigUpdate,
    FeedbackOut,
    WallpaperUpdate,
    WallpaperBatchUpdate,
    DebugConfigOut,
    DebugConfigUpdate,
    DebugLogOut,
    DebugLogList,
    SiteConfigOut,
    SiteConfigUpdate,
)
from backend.auth import require_admin, hash_password
from backend.routers.wallpapers import _wallpaper_to_out, _save_wallpaper_upload
from backend import webhook
from backend.verification import get_auth_config, get_smtp_credentials, get_sms_credentials

router = APIRouter(prefix="/admin", tags=["管理"])


# ─── Wallpaper submissions (approve/reject) ───────────────────────────────────


@router.get("/submissions", response_model=WallpaperList)
def admin_list_submissions(
    status: str = Query("pending"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    device_type: Optional[DeviceType] = Query(None),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Wallpaper)
    if status == "pending":
        q = q.filter(Wallpaper.status == WallpaperStatus.PENDING)
    elif status == "approved":
        q = q.filter(Wallpaper.status == WallpaperStatus.APPROVED)
    elif status == "rejected":
        q = q.filter(Wallpaper.status == WallpaperStatus.REJECTED)
    elif status == "unlisted":
        q = q.filter(Wallpaper.status == WallpaperStatus.UNLISTED)
    elif status == "all":
        pass  # show all
    if device_type:
        q = q.join(Wallpaper.device_types).filter(WallpaperDeviceType.device_type == device_type)
    q = q.order_by(Wallpaper.created_at.desc())

    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return WallpaperList(
        items=[_wallpaper_to_out(w) for w in items],
        total=total, page=page, size=size, pages=ceil(total / size) if total > 0 else 1,
    )


@router.post("/submissions/{wallpaper_id}")
def admin_review(
    wallpaper_id: int,
    body: ApproveRequest,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="壁纸不存在")

    wp.status = WallpaperStatus.APPROVED if body.approve else WallpaperStatus.REJECTED
    wp.reject_reason = body.reject_reason if not body.approve else None
    db.commit()

    # Notify via webhook (do not block the response)
    webhook.send_webhook_async(
        db,
        "wallpaper_reviewed",
        {
            "id": wp.id,
            "title": wp.title,
            "approved": body.approve,
            "reject_reason": body.reject_reason,
        },
    )

    return {"ok": True, "status": wp.status.value}


# ─── Wallpaper status change (unlist / relist) ────────────────────────────────


@router.put("/wallpapers/{wallpaper_id}/status")
def admin_change_wallpaper_status(
    wallpaper_id: int,
    body: WallpaperStatusChange,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="壁纸不存在")

    new_status = WallpaperStatus(body.status)
    wp.status = new_status
    if new_status == WallpaperStatus.REJECTED:
        wp.reject_reason = body.reject_reason
    else:
        wp.reject_reason = None
    db.commit()
    return {"ok": True, "status": wp.status.value}


# ─── Admin wallpapers list (all statuses) ─────────────────────────────────────


@router.get("/wallpapers", response_model=WallpaperList)
def admin_list_wallpapers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    status: Optional[str] = Query(None),
    device_type: Optional[DeviceType] = Query(None),
    search: Optional[str] = Query(None),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Wallpaper)
    if status:
        try:
            q = q.filter(Wallpaper.status == WallpaperStatus(status))
        except ValueError:
            pass
    if device_type:
        q = q.join(Wallpaper.device_types).filter(WallpaperDeviceType.device_type == device_type)
    if search:
        from sqlalchemy import or_
        q = q.filter(Wallpaper.title.ilike(f"%{search}%"))
    q = q.order_by(Wallpaper.created_at.desc())

    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return WallpaperList(
        items=[_wallpaper_to_out(w) for w in items],
        total=total, page=page, size=size, pages=ceil(total / size) if total > 0 else 1,
    )


# ─── Admin upload ──────────────────────────────────────────────────────────────


@router.post("/wallpapers", response_model=WallpaperOut)
def admin_upload_wallpaper(
    title: str = Form(...),
    device_types: str = Form("portrait"),
    device_type: Optional[str] = Form(None),
    category_id: int = Form(None),
    category_ids: str = Form(""),
    tags: str = Form(""),
    description: str = Form(None),
    file: UploadFile = File(...),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """管理员上传壁纸，直接 approved 上架。"""
    raw = device_types
    if device_type and device_type != raw:
        raw = device_type
    dt_list = [DeviceType(d.strip()) for d in raw.split(",") if d.strip()]

    cid_list: list[int] = []
    if category_ids:
        cid_list = [int(c.strip()) for c in category_ids.split(",") if c.strip().isdigit()]
    if not cid_list and category_id:
        cid_list = [category_id]

    wp = _save_wallpaper_upload(
        file=file,
        title=title,
        device_types=dt_list,
        category_ids=cid_list,
        tags=tags,
        description=description,
        author_id=admin.id,
        status=WallpaperStatus.APPROVED,
        db=db,
    )
    return _wallpaper_to_out(wp)


# ─── Category Management ──────────────────────────────────────────────────────


@router.get("/categories", response_model=CategoriesList)
def admin_list_categories(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cats = db.query(Category).order_by(Category.sort).all()
    return CategoriesList(items=[CategoryOut.model_validate(c) for c in cats])


@router.post("/categories", response_model=CategoryOut)
def admin_create_category(
    data: CategoryCreate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(Category).filter(
        (Category.slug == data.slug) | (Category.name == data.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类名称或slug已存在")

    cat = Category(name=data.name, slug=data.slug, icon=data.icon, sort=data.sort or 0)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.put("/categories/{category_id}", response_model=CategoryOut)
def admin_update_category(
    category_id: int,
    data: CategoryUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")

    if data.name is not None:
        dup = db.query(Category).filter(Category.name == data.name, Category.id != category_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="分类名称已存在")
        cat.name = data.name
    if data.slug is not None:
        dup = db.query(Category).filter(Category.slug == data.slug, Category.id != category_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="分类slug已存在")
        cat.slug = data.slug
    if data.icon is not None:
        cat.icon = data.icon
    if data.sort is not None:
        cat.sort = data.sort

    db.commit()
    db.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.delete("/categories/{category_id}")
def admin_delete_category(
    category_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")

    wp_count = db.query(WallpaperCategory).filter(WallpaperCategory.category_id == category_id).count()
    if wp_count > 0:
        raise HTTPException(status_code=400, detail=f"该分类下还有 {wp_count} 张壁纸，请先移动或删除")

    db.delete(cat)
    db.commit()
    return {"ok": True}


# ─── Users Management ─────────────────────────────────────────────────────────


@router.get("/users", response_model=List[UserOut])
def admin_list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User).order_by(User.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return [UserOut.model_validate(u) for u in items]


@router.get("/users/{user_id}", response_model=UserOut)
def admin_get_user(
    user_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserOut.model_validate(user)


@router.put("/users/{user_id}", response_model=UserOut)
def admin_update_user(
    user_id: int,
    data: UserAdminUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == admin.id and data.is_admin is False:
        raise HTTPException(status_code=400, detail="不能取消自己的管理员权限")
    user.is_admin = data.is_admin
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    force: bool = Query(False, description="强制删除（含该用户所有壁纸）"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    wp_count = db.query(Wallpaper).filter(Wallpaper.author_id == user.id).count()
    if wp_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"该用户有 {wp_count} 张壁纸，无法直接删除。请先处理其壁纸后再删，或传 force=true 强制级联删除。"
        )

    if wp_count > 0:
        # 清理收藏、点赞关联，再清理壁纸文件
        from backend.routers.wallpapers import _delete_wallpaper_files
        from backend.models import Favorite, Like
        wps = db.query(Wallpaper).filter(Wallpaper.author_id == user.id).all()
        wp_ids = [wp.id for wp in wps]
        if wp_ids:
            db.query(Favorite).filter(Favorite.wallpaper_id.in_(wp_ids)).delete(synchronize_session=False)
            db.query(Like).filter(Like.wallpaper_id.in_(wp_ids)).delete(synchronize_session=False)
        for wp in wps:
            _delete_wallpaper_files(db, wp)
            db.delete(wp)
        db.flush()

    # 清理用户自己的关联记录（收藏/点赞/反馈/验证码等 FK 约束）
    from backend.models import Favorite, Like, Feedback, VerificationCode
    db.query(Favorite).filter(Favorite.user_id == user.id).delete(synchronize_session=False)
    db.query(Like).filter(Like.user_id == user.id).delete(synchronize_session=False)
    db.query(Feedback).filter(Feedback.user_id == user.id).delete(synchronize_session=False)
    db.query(VerificationCode).filter(VerificationCode.target == user.email).delete(synchronize_session=False)
    if user.phone:
        db.query(VerificationCode).filter(VerificationCode.target == user.phone).delete(synchronize_session=False)

    db.delete(user)
    db.commit()
    return {"ok": True, "wallpapers_deleted": wp_count if force else 0}


@router.get("/users/{user_id}/wallpapers", response_model=WallpaperList)
def admin_list_user_wallpapers(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """查看指定用户上传的所有壁纸。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    q = db.query(Wallpaper).filter(Wallpaper.author_id == user_id).order_by(Wallpaper.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return WallpaperList(
        items=[_wallpaper_to_out(w) for w in items],
        total=total, page=page, size=size, pages=ceil(total / size) if total > 0 else 1,
    )


@router.post("/users/{user_id}/reassign-wallpapers")
def admin_reassign_wallpapers(
    user_id: int,
    target_user_id: int = Query(..., description="目标用户 ID，壁纸将归属此用户"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """将某用户的所有壁纸转移给另一用户（用于删除用户前迁移壁纸）。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="源用户不存在")
    if user_id == target_user_id:
        raise HTTPException(status_code=400, detail="源用户和目标用户不能相同")

    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    count = db.query(Wallpaper).filter(Wallpaper.author_id == user_id).update(
        {"author_id": target_user_id}, synchronize_session=False
    )
    db.commit()
    return {"ok": True, "reassigned": count, "from_user": user.username, "to_user": target.username}


@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    body: ResetPassword,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"ok": True, "message": "密码已重置"}


# ─── Webhook ──────────────────────────────────────────────────────────────────


@router.get("/config/webhook", response_model=WebhookConfigOut)
def admin_get_webhook_config(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    url = webhook.get_webhook_url(db)
    return WebhookConfigOut(url=url)


@router.put("/config/webhook", response_model=WebhookConfigOut)
def admin_update_webhook_config(
    data: WebhookConfigUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = db.query(WebhookConfig).filter(WebhookConfig.id == 1).first()
    if not cfg:
        cfg = WebhookConfig(id=1, url=data.url)
        db.add(cfg)
    else:
        cfg.url = data.url
    db.commit()
    db.refresh(cfg)
    return WebhookConfigOut(url=cfg.url)


@router.post("/webhook-test")
def admin_webhook_test(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return webhook.send_webhook(db, "test", {"message": "管理员刚刚点击了测试 Webhook 按钮。"})


# ─── Auth Config ──────────────────────────────────────────────────────────────


@router.get("/config/auth", response_model=AuthConfigOut)
def admin_get_auth_config(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return AuthConfigOut.model_validate(get_auth_config(db))


@router.put("/config/auth", response_model=AuthConfigOut)
def admin_update_auth_config(
    data: AuthConfigUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = get_auth_config(db)
    if data.enable_email_verify is not None:
        cfg.enable_email_verify = data.enable_email_verify
    if data.enable_sms_verify is not None:
        cfg.enable_sms_verify = data.enable_sms_verify
    if data.require_email is not None:
        cfg.require_email = data.require_email
    if data.email_provider is not None:
        cfg.email_provider = data.email_provider
    if data.sms_provider is not None:
        cfg.sms_provider = data.sms_provider
    if data.enable_huawei_login is not None:
        cfg.enable_huawei_login = data.enable_huawei_login
    db.commit()
    db.refresh(cfg)
    return AuthConfigOut.model_validate(cfg)


# ─── Storage Config ───────────────────────────────────────────────────────────


def _get_or_create(db: Session, model, defaults: dict):
    cfg = db.query(model).order_by(model.id).first()
    if not cfg:
        cfg = model(**defaults)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _apply_update(cfg, data, fields):
    for field in fields:
        value = getattr(data, field, None)
        if value is not None:
            setattr(cfg, field, value)


@router.get("/config/storage", response_model=StorageConfigOut)
def admin_get_storage_config(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = _get_or_create(db, StorageConfig, {"provider": "local", "enabled": False})
    return StorageConfigOut.model_validate(cfg)


@router.put("/config/storage", response_model=StorageConfigOut)
def admin_update_storage_config(
    data: StorageConfigUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = _get_or_create(db, StorageConfig, {"provider": "local", "enabled": False})
    _apply_update(cfg, data, (
        "provider", "bucket", "endpoint", "region", "access_key",
        "secret_key", "cdn_domain", "path_prefix", "signed_url", "enabled",
    ))
    db.commit()
    db.refresh(cfg)
    return StorageConfigOut.model_validate(cfg)


# ─── SMTP Config ──────────────────────────────────────────────────────────────


@router.get("/config/smtp", response_model=SmtpConfigOut)
def admin_get_smtp_config(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = _get_or_create(db, SmtpConfig, {"enabled": False})
    return SmtpConfigOut.model_validate(cfg)


@router.put("/config/smtp", response_model=SmtpConfigOut)
def admin_update_smtp_config(
    data: SmtpConfigUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = _get_or_create(db, SmtpConfig, {"enabled": False})
    _apply_update(cfg, data, (
        "host", "port", "user", "password", "use_tls",
        "from_addr", "from_name", "enabled",
    ))
    db.commit()
    db.refresh(cfg)
    return SmtpConfigOut.model_validate(cfg)


# ─── SMS Config ───────────────────────────────────────────────────────────────


@router.get("/config/sms", response_model=SmsConfigOut)
def admin_get_sms_config(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = _get_or_create(db, SmsConfig, {"enabled": False})
    return SmsConfigOut.model_validate(cfg)


@router.put("/config/sms", response_model=SmsConfigOut)
def admin_update_sms_config(
    data: SmsConfigUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = _get_or_create(db, SmsConfig, {"enabled": False})
    _apply_update(cfg, data, (
        "provider", "aliyun_access_key_id", "aliyun_access_key_secret",
        "aliyun_sign_name", "aliyun_template_code", "yunpian_api_key", "enabled",
    ))
    db.commit()
    db.refresh(cfg)
    return SmsConfigOut.model_validate(cfg)


# ─── Admin Password Reset ─────────────────────────────────────────────────────


@router.post("/reset-my-password")
def admin_reset_my_password(
    body: ResetPassword,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    admin.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"ok": True, "message": "密码已重置"}


# ─── Site Config ──────────────────────────────────────────────────────────────


@router.get("/config/site", response_model=SiteConfigOut)
def admin_get_site_config(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from backend.models import SiteConfig
    cfg = db.query(SiteConfig).filter(SiteConfig.id == 1).first()
    if not cfg:
        cfg = SiteConfig(id=1, upload_enabled=True)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return SiteConfigOut.model_validate(cfg)


@router.put("/config/site", response_model=SiteConfigOut)
def admin_update_site_config(
    data: SiteConfigUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from backend.models import SiteConfig
    cfg = db.query(SiteConfig).filter(SiteConfig.id == 1).first()
    if not cfg:
        cfg = SiteConfig(id=1, upload_enabled=data.upload_enabled)
        db.add(cfg)
    else:
        cfg.upload_enabled = data.upload_enabled
    db.commit()
    db.refresh(cfg)
    return SiteConfigOut.model_validate(cfg)


# ─── Feedback Management ──────────────────────────────────────────────────────


@router.get("/feedback", response_model=List[FeedbackOut])
def admin_list_feedback(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Feedback).order_by(Feedback.created_at.desc())
    items = q.offset((page - 1) * size).limit(size).all()
    return [FeedbackOut.model_validate(f) for f in items]


@router.delete("/feedback/{feedback_id}")
def admin_delete_feedback(
    feedback_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="反馈不存在")
    db.delete(fb)
    db.commit()
    return {"ok": True}


@router.put("/wallpapers/{wallpaper_id}/categories", response_model=WallpaperOut)
def admin_update_wallpaper_categories(
    wallpaper_id: int,
    data: WallpaperUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """审核时单独修改壁纸分类（支持多选）。"""
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="壁纸不存在")
    _apply_categories(db, wp, data.category_ids)
    db.commit()
    db.refresh(wp)
    return _wallpaper_to_out(wp)


# ─── Wallpaper Edit (single & batch) ──────────────────────────────────────────


def _apply_categories(db: Session, wp: Wallpaper, category_ids: list[int] | None):
    """Replace wallpaper's categories when category_ids is provided (non-empty)."""
    if category_ids is None:
        return
    category_ids = [cid for cid in category_ids if cid]
    if not category_ids:
        return
    # Validate all categories exist
    existing = db.query(Category).filter(Category.id.in_(category_ids)).count()
    if existing != len(category_ids):
        raise HTTPException(status_code=400, detail="分类不存在")
    db.query(WallpaperCategory).filter(WallpaperCategory.wallpaper_id == wp.id).delete()
    for cid in category_ids:
        db.add(WallpaperCategory(wallpaper_id=wp.id, category_id=cid))
    wp.category_id = category_ids[0]


@router.put("/wallpapers/{wallpaper_id}", response_model=WallpaperOut)
def admin_update_wallpaper(
    wallpaper_id: int,
    data: WallpaperUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    wp = db.query(Wallpaper).filter(Wallpaper.id == wallpaper_id).first()
    if not wp:
        raise HTTPException(status_code=404, detail="壁纸不存在")

    if data.title is not None:
        wp.title = data.title
    if data.description is not None:
        wp.description = data.description
    if data.category_id is not None:
        wp.category_id = data.category_id
    _apply_categories(db, wp, data.category_ids)
    if data.device_types is not None:
        db.query(WallpaperDeviceType).filter(WallpaperDeviceType.wallpaper_id == wp.id).delete()
        for dt in data.device_types:
            db.add(WallpaperDeviceType(wallpaper_id=wp.id, device_type=dt))
    if data.tags is not None:
        wp.tags = data.tags

    db.commit()
    db.refresh(wp)
    return _wallpaper_to_out(wp)


@router.post("/wallpapers/batch")
def admin_batch_update_wallpapers(
    data: WallpaperBatchUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    updated = 0
    for wid in data.ids:
        wp = db.query(Wallpaper).filter(Wallpaper.id == wid).first()
        if wp:
            if data.title is not None:
                wp.title = data.title
            if data.description is not None:
                wp.description = data.description
            if data.category_id is not None:
                wp.category_id = data.category_id
            _apply_categories(db, wp, data.category_ids)
            if data.device_types is not None:
                db.query(WallpaperDeviceType).filter(WallpaperDeviceType.wallpaper_id == wp.id).delete()
                for dt in data.device_types:
                    db.add(WallpaperDeviceType(wallpaper_id=wp.id, device_type=dt))
            if data.tags is not None:
                wp.tags = data.tags
            updated += 1
    db.commit()
    return {"ok": True, "updated": updated, "requested": len(data.ids)}


# ─── Test Endpoints ────────────────────────────────────────────────────────────

import os as _os, tempfile as _tempfile
from backend.storage import get_storage as _get_storage


@router.post("/test-storage")
def admin_test_storage(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """测试对象存储连通性——写入临时文件后读取验证。"""
    fd, tmp_path = _tempfile.mkstemp(suffix=".txt")
    try:
        storage = _get_storage(db)
        test_key = f"_admin_test_{admin.id}.txt"
        test_content = f"Storage connectivity test by admin {admin.username}"
        _os.write(fd, test_content.encode("utf-8"))
        _os.close(fd)
        test_url = storage.save(tmp_path, test_key)
        try:
            _os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        return {"ok": True, "message": f"存储连通正常 ✓\n测试文件: {test_url}"}
    except Exception as e:
        try:
            _os.unlink(tmp_path)
        except Exception:
            pass
        return {"ok": False, "message": f"存储测试失败: {str(e)}"}


@router.post("/test-smtp")
def admin_test_smtp(
    to_email: str = Query(..., description="接收测试邮件的邮箱地址"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """使用当前 SMTP 配置发送测试邮件。"""
    from backend.email import send_email_code
    try:
        cfg = get_smtp_credentials(db)
        host = cfg.get("host") or _os.getenv("EMAIL_SMTP_HOST")
        if not host:
            return {"ok": False, "message": "SMTP 未配置，请先在邮箱配置中填写 SMTP 服务器"}
        success = send_email_code(to_email, "888888", cfg)
        if success:
            return {"ok": True, "message": f"测试邮件已发送到 {to_email}，请查收"}
        return {"ok": False, "message": "发送失败，请检查 SMTP 服务器/端口/账号/授权码是否正确"}
    except Exception as e:
        return {"ok": False, "message": f"邮件测试异常: {str(e)}"}


@router.post("/test-sms")
def admin_test_sms(
    phone: str = Query(..., description="接收测试短信的手机号"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """使用当前短信平台配置发送测试短信。"""
    from backend.sms import send_sms_code
    try:
        cfg = get_sms_credentials(db)
        provider = cfg.get("provider") or "aliyun"
        if provider == "aliyun" and not cfg.get("access_key_id"):
            return {"ok": False, "message": "阿里云短信 AccessKey 未配置"}
        if provider == "yunpian" and not cfg.get("api_key"):
            return {"ok": False, "message": "云片 API KEY 未配置"}
        success = send_sms_code(phone, "888888", provider, cfg)
        if success:
            return {"ok": True, "message": f"测试短信已发送到 {phone}，请查收"}
        return {"ok": False, "message": "发送失败，请检查短信平台配置（签名/模板/余额）"}
    except Exception as e:
        return {"ok": False, "message": f"短信测试异常: {str(e)}"}


# ─── Debug Config ─────────────────────────────────────────────────────────────


@router.get("/config/debug", response_model=DebugConfigOut)
def admin_get_debug_config(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = db.query(DebugConfig).filter(DebugConfig.id == 1).first()
    if not cfg:
        cfg = DebugConfig(id=1, enabled=False, log_retention_days=7)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return DebugConfigOut.model_validate(cfg)


@router.put("/config/debug", response_model=DebugConfigOut)
def admin_update_debug_config(
    data: DebugConfigUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    cfg = db.query(DebugConfig).filter(DebugConfig.id == 1).first()
    if not cfg:
        cfg = DebugConfig(id=1, enabled=False, log_retention_days=7)
        db.add(cfg)
    if data.enabled is not None:
        cfg.enabled = data.enabled
    if data.log_retention_days is not None:
        cfg.log_retention_days = data.log_retention_days
    db.commit()
    db.refresh(cfg)
    return DebugConfigOut.model_validate(cfg)


# ─── Debug Logs ────────────────────────────────────────────────────────────────


@router.get("/debug-logs", response_model=DebugLogList)
def admin_list_debug_logs(
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=200),
    search: Optional[str] = Query(None),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(DebugLog)
    if search:
        q = q.filter(DebugLog.path.ilike(f"%{search}%"))
    q = q.order_by(DebugLog.created_at.desc())

    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return DebugLogList(
        items=[DebugLogOut.model_validate(log) for log in items],
        total=total,
        page=page,
    )


@router.delete("/debug-logs")
def admin_clear_debug_logs(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """清空所有调试日志。"""
    count = db.query(DebugLog).count()
    db.query(DebugLog).delete()
    db.commit()
    return {"ok": True, "deleted": count}


@router.delete("/debug-logs/expired")
def admin_clean_expired_logs(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """按 DebugConfig.log_retention_days 清理过期日志。"""
    cfg = db.query(DebugConfig).filter(DebugConfig.id == 1).first()
    days = cfg.log_retention_days if cfg else 7
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    count = db.query(DebugLog).filter(DebugLog.created_at < cutoff).delete()
    db.commit()
    return {"ok": True, "deleted": count, "retention_days": days}
