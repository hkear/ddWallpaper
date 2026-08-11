from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from backend.models import DeviceType, WallpaperStatus


# ── User ──────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    phone: Optional[str] = Field(None, max_length=20)
    verification_code: Optional[str] = Field(None, max_length=10)  # 兼容旧版单一验证码
    email_code: Optional[str] = Field(None, max_length=10)
    sms_code: Optional[str] = Field(None, max_length=10)


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserAdminUpdate(BaseModel):
    is_admin: bool


class ResetPassword(BaseModel):
    new_password: str = Field(..., min_length=6)


class SendCodeRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=100)


class HuaweiLoginRequest(BaseModel):
    access_token: str = Field(..., min_length=1)
    open_id: Optional[str] = None


class AuthConfigOut(BaseModel):
    enable_email_verify: bool = False
    enable_sms_verify: bool = False
    require_email: bool = True
    email_provider: str = "smtp"
    sms_provider: str = "aliyun"
    enable_huawei_login: bool = False

    class Config:
        from_attributes = True


class AuthConfigUpdate(BaseModel):
    enable_email_verify: Optional[bool] = None
    enable_sms_verify: Optional[bool] = None
    require_email: Optional[bool] = None
    email_provider: Optional[str] = None
    sms_provider: Optional[str] = None
    enable_huawei_login: Optional[bool] = None


class WebhookConfigOut(BaseModel):
    url: str

    class Config:
        from_attributes = True


class WebhookConfigUpdate(BaseModel):
    url: str = Field(..., min_length=1, max_length=500)


class StorageConfigOut(BaseModel):
    provider: str = "local"
    bucket: Optional[str] = None
    endpoint: Optional[str] = None
    region: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    cdn_domain: Optional[str] = None
    path_prefix: str = "wallpapers/"
    signed_url: bool = False
    enabled: bool = False

    class Config:
        from_attributes = True


class StorageConfigUpdate(BaseModel):
    provider: Optional[str] = None
    bucket: Optional[str] = None
    endpoint: Optional[str] = None
    region: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    cdn_domain: Optional[str] = None
    path_prefix: Optional[str] = None
    signed_url: Optional[bool] = None
    enabled: Optional[bool] = None


class SmtpConfigOut(BaseModel):
    host: Optional[str] = None
    port: int = 465
    user: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    from_addr: Optional[str] = None
    from_name: Optional[str] = "多点壁纸"
    enabled: bool = False

    class Config:
        from_attributes = True


class SmtpConfigUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    use_tls: Optional[bool] = None
    from_addr: Optional[str] = None
    from_name: Optional[str] = None
    enabled: Optional[bool] = None


class SmsConfigOut(BaseModel):
    provider: str = "aliyun"
    aliyun_access_key_id: Optional[str] = None
    aliyun_access_key_secret: Optional[str] = None
    aliyun_sign_name: Optional[str] = None
    aliyun_template_code: Optional[str] = None
    yunpian_api_key: Optional[str] = None
    enabled: bool = False

    class Config:
        from_attributes = True


class SmsConfigUpdate(BaseModel):
    provider: Optional[str] = None
    aliyun_access_key_id: Optional[str] = None
    aliyun_access_key_secret: Optional[str] = None
    aliyun_sign_name: Optional[str] = None
    aliyun_template_code: Optional[str] = None
    yunpian_api_key: Optional[str] = None
    enabled: Optional[bool] = None


# ── Category ─────────────────────────────────────────────────────────────────
class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    icon: Optional[str] = None
    sort: int = 0

    class Config:
        from_attributes = True


class CategoriesList(BaseModel):
    items: list[CategoryOut]


# ── Wallpaper ─────────────────────────────────────────────────────────────────
class WallpaperOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    device_type: DeviceType
    category_id: int
    tags: list[str] = []
    resolution: Optional[str] = None
    file_size: int = 0
    original_url: str
    thumbnail_1080_url: Optional[str] = None
    thumbnail_720_url: Optional[str] = None
    thumbnail_small_url: Optional[str] = None
    format: str = "jpg"
    width: int = 0
    height: int = 0
    downloads: int = 0
    likes: int = 0
    status: WallpaperStatus
    author_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WallpaperList(BaseModel):
    items: list[WallpaperOut]
    total: int
    page: int
    size: int
    pages: int


class WallpaperUpload(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    device_type: DeviceType = DeviceType.PORTRAIT
    category_id: int
    tags: list[str] = []
    description: Optional[str] = None


# ── Like ──────────────────────────────────────────────────────────────────────
class LikeOut(BaseModel):
    likes: int
    liked: bool


# ── Submission list ────────────────────────────────────────────────────────────
class SubmissionList(BaseModel):
    items: list[WallpaperOut]
    total: int
    pages: int


# ── Category CRUD ───────────────────────────────────────────────────────────────
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)
    icon: Optional[str] = None
    sort: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    icon: Optional[str] = None
    sort: Optional[int] = None


# ── Admin ─────────────────────────────────────────────────────────────────────
class ApproveRequest(BaseModel):
    approve: bool
    reject_reason: Optional[str] = None


class WallpaperStatusChange(BaseModel):
    status: str = Field(..., pattern=r'^(approved|rejected|unlisted)$')
    reject_reason: Optional[str] = None


# ── Feedback ──────────────────────────────────────────────────────────────────
class FeedbackCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)


class FeedbackOut(BaseModel):
    id: int
    name: str
    email: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class WallpaperUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    device_type: Optional[DeviceType] = None
    tags: Optional[list[str]] = None


class WallpaperBatchUpdate(BaseModel):
    ids: list[int]
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    device_type: Optional[DeviceType] = None
    tags: Optional[list[str]] = None
