import os
from typing import Optional

import httpx

from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import (
    UserCreate, UserOut, Token, PasswordChange,
    SendCodeRequest, HuaweiLoginRequest, SiteConfigOut,
)
from backend.auth import hash_password, verify_password, create_access_token, get_current_user
from backend.verification import get_auth_config, send_verification_code, verify_code
from backend.huawei_oauth import huawei_get_user_info
from backend.webhook import notify_admin
from backend.config import get_settings
from backend.database import SessionLocal
from PIL import Image as PILImage
import io

router = APIRouter(prefix="/users", tags=["用户"])
settings = get_settings()

AVATAR_MAX_SIZE = 256
AVATAR_MAX_BYTES = 5 * 1024 * 1024
AVATAR_ALLOWED_EXT = {"jpg", "jpeg", "png", "webp", "gif"}


def _avatar_ext(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.split(".")[-1].lower()


def _token_response(user: User) -> Token:
    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/auth-config", response_model=dict)
def get_public_auth_config(db: Session = Depends(get_db)):
    """Public auth config (what frontend needs to know)."""
    config = get_auth_config(db)
    return {
        "require_email": config.require_email,
        "enable_email_verify": config.enable_email_verify,
        "enable_sms_verify": config.enable_sms_verify,
        "enable_huawei_login": config.enable_huawei_login,
    }


@router.post("/send-email-code")
def send_email_code_endpoint(req: SendCodeRequest, db: Session = Depends(get_db)):
    config = get_auth_config(db)
    if not config.enable_email_verify:
        raise HTTPException(status_code=400, detail="邮箱验证码未启用")

    target = req.target.strip().lower()
    _, ok = send_verification_code(db, target, "email")
    if not ok:
        raise HTTPException(status_code=500, detail="验证码发送失败，请检查邮箱配置")
    return {"ok": True, "message": "验证码已发送"}


@router.post("/send-sms-code")
def send_sms_code_endpoint(req: SendCodeRequest, db: Session = Depends(get_db)):
    config = get_auth_config(db)
    if not config.enable_sms_verify:
        raise HTTPException(status_code=400, detail="短信验证码未启用")

    target = req.target.strip()
    _, ok = send_verification_code(db, target, "sms")
    if not ok:
        raise HTTPException(status_code=500, detail="验证码发送失败，请检查短信配置")
    return {"ok": True, "message": "验证码已发送"}


@router.post("/register", response_model=Token)
def register(data: UserCreate, db: Session = Depends(get_db)):
    config = get_auth_config(db)

    # Username unique check
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # Email required / unique
    email = data.email.strip().lower() if data.email else ""
    if config.require_email and not email:
        raise HTTPException(status_code=400, detail="邮箱必填")
    if email:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

    # Email verification code check
    if config.enable_email_verify:
        email_code = (data.email_code or data.verification_code or "").strip()
        if not email_code:
            raise HTTPException(status_code=400, detail="请输入邮箱验证码")
        if not verify_code(db, email, "email", email_code):
            raise HTTPException(status_code=400, detail="邮箱验证码错误或已过期")

    # SMS verification code check
    phone = (data.phone or "").strip()
    if config.enable_sms_verify:
        sms_code = (data.sms_code or data.verification_code or "").strip()
        if not phone or not sms_code:
            raise HTTPException(status_code=400, detail="请输入手机号和短信验证码")
        if not verify_code(db, phone, "sms", sms_code):
            raise HTTPException(status_code=400, detail="短信验证码错误或已过期")

    user = User(
        username=data.username,
        email=email,
        phone=phone or None,
        hashed_password=hash_password(data.password),
        email_verified=config.enable_email_verify,
        phone_verified=config.enable_sms_verify,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    notify_admin(f"新用户注册：{user.username} ({user.email or '无邮箱'})")
    return _token_response(user)


@router.post("/login", response_model=Token)
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/huawei-login", response_model=Token)
def huawei_login(data: HuaweiLoginRequest, db: Session = Depends(get_db)):
    config = get_auth_config(db)
    if not config.enable_huawei_login:
        raise HTTPException(status_code=400, detail="华为账号登录未启用")

    huawei_user = huawei_get_user_info(data.access_token)
    if not huawei_user:
        raise HTTPException(status_code=401, detail="华为账号授权失败")

    open_id = data.open_id or huawei_user.get("openid") or huawei_user.get("unionId")
    if not open_id:
        raise HTTPException(status_code=400, detail="无法获取华为账号标识")

    user = db.query(User).filter(User.huawei_open_id == open_id).first()
    if not user:
        # Auto-create user bound to Huawei account
        display_name = huawei_user.get("displayName") or huawei_user.get("nickname") or f"hw_{open_id[:8]}"
        base_name = display_name[:50]
        username = base_name
        counter = 1
        while db.query(User).filter(User.username == username).first():
            suffix = f"_{counter}"
            username = base_name[: 50 - len(suffix)] + suffix
            counter += 1

        user = User(
            username=username,
            email=f"{open_id}@huawei.user",
            hashed_password=hash_password(os.urandom(24).hex()),
            huawei_open_id=open_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return _token_response(user)


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.get("/config", response_model=SiteConfigOut)
def get_public_site_config(db: Session = Depends(get_db)):
    """Public site config (what frontend needs to know)."""
    from backend.models import SiteConfig
    cfg = db.query(SiteConfig).filter(SiteConfig.id == 1).first()
    if not cfg:
        cfg = SiteConfig(id=1, upload_enabled=True)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return SiteConfigOut.model_validate(cfg)


@router.post("/me/avatar", response_model=UserOut)
def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload/change current user's avatar. Resizes/crops to <=256x256, keeps only processed image."""
    ext = _avatar_ext(file.filename or "")
    if ext not in AVATAR_ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="请选择图片文件（jpg/png/webp/gif）")

    content = file.file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="空文件")
    if len(content) > AVATAR_MAX_BYTES:
        raise HTTPException(status_code=400, detail="头像文件超过5MB限制")

    try:
        img = PILImage.open(io.BytesIO(content))
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法读取图片: {e}")

    # Crop to square (center) then resize to max 256x256
    width, height = img.size
    if width != height:
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        img = img.crop((left, top, left + side, top + side))
    if max(img.size) > AVATAR_MAX_SIZE:
        img.thumbnail((AVATAR_MAX_SIZE, AVATAR_MAX_SIZE), PILImage.Resampling.LANCZOS)

    avatar_dir = os.path.join(settings.UPLOAD_DIR, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)

    # Remove old avatar file if present
    if user.avatar_url:
        old_key = user.avatar_url.replace("/static/", "")
        old_path = os.path.join(settings.UPLOAD_DIR, old_key)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    out_name = f"{user.id}.jpg"
    out_path = os.path.join(avatar_dir, out_name)
    img.save(out_path, "JPEG", quality=85, optimize=True)

    user.avatar_url = f"/static/avatars/{out_name}"
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/me/change-password")
def change_password(
    data: PasswordChange,
    user: User = Depends(__import__("backend.auth", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="原密码错误")
    if data.old_password == data.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"ok": True, "message": "密码修改成功"}
