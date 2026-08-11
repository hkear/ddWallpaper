from sqlalchemy import (
    Column, Integer, String, Text, Enum, DateTime, ForeignKey,
    BigInteger, Boolean, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import enum


class DeviceType(str, enum.Enum):
    PORTRAIT = "portrait"     # 竖屏
    LANDSCAPE = "landscape"   # 横屏
    FOLD2 = "fold2"           # 两折叠
    FOLD3 = "fold3"          # 三折叠


class WallpaperStatus(str, enum.Enum):
    PENDING = "pending"    # 待审核
    APPROVED = "approved"   # 已通过
    REJECTED = "rejected"   # 已拒绝
    UNLISTED = "unlisted"   # 已下架


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    huawei_open_id = Column(String(100), unique=True, nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relations
    wallpapers = relationship("Wallpaper", back_populates="author", lazy="dynamic")
    favorites = relationship("Favorite", back_populates="user", lazy="dynamic")


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String(100), nullable=False, index=True)  # email or phone
    code_type = Column(String(20), nullable=False)  # 'email' or 'sms'
    code = Column(String(10), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)


class AuthConfig(Base):
    __tablename__ = "auth_config"

    id = Column(Integer, primary_key=True)
    enable_email_verify = Column(Boolean, default=False)
    enable_sms_verify = Column(Boolean, default=False)
    require_email = Column(Boolean, default=True)
    email_provider = Column(String(20), default="smtp")
    sms_provider = Column(String(20), default="aliyun")
    enable_huawei_login = Column(Boolean, default=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    icon = Column(String(20), nullable=True)
    sort = Column(Integer, default=0)

    wallpapers = relationship("WallpaperCategory", back_populates="category", lazy="dynamic")


class Wallpaper(Base):
    __tablename__ = "wallpapers"
    __table_args__ = (
        Index("ix_wallpapers_status", "status"),
        Index("ix_wallpapers_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    tags = Column(JSON, nullable=True, default=list)  # ["夕阳", "海边"]

    # File info
    original_url = Column(String(500), nullable=False)
    thumbnail_1080_url = Column(String(500), nullable=True)
    thumbnail_720_url = Column(String(500), nullable=True)
    thumbnail_small_url = Column(String(500), nullable=True)
    file_size = Column(BigInteger, default=0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    resolution = Column(String(20), nullable=True)  # e.g. "1080x2340"
    format = Column(String(10), default="jpg")

    # Stats
    downloads = Column(Integer, default=0)
    likes = Column(Integer, default=0)

    # Status & author
    status = Column(Enum(WallpaperStatus), default=WallpaperStatus.PENDING)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reject_reason = Column(String(500), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    author = relationship("User", back_populates="wallpapers")
    categories = relationship("WallpaperCategory", back_populates="wallpaper", lazy="joined",
                              cascade="all, delete-orphan")
    favorited_by = relationship("Favorite", back_populates="wallpaper", lazy="dynamic")
    liked_by = relationship("Like", back_populates="wallpaper", lazy="dynamic")
    device_types = relationship("WallpaperDeviceType", back_populates="wallpaper", lazy="joined",
                                cascade="all, delete-orphan")


class WallpaperDeviceType(Base):
    """Junction table: wallpaper many-to-many device_type"""
    __tablename__ = "wallpaper_device_types"
    __table_args__ = (
        UniqueConstraint("wallpaper_id", "device_type", name="uq_wp_device_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    wallpaper_id = Column(Integer, ForeignKey("wallpapers.id"), nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)

    wallpaper = relationship("Wallpaper", back_populates="device_types")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallpaper_id = Column(Integer, ForeignKey("wallpapers.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "wallpaper_id", name="uq_user_wallpaper"),)

    user = relationship("User", back_populates="favorites")
    wallpaper = relationship("Wallpaper", back_populates="favorited_by")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallpaper_id = Column(Integer, ForeignKey("wallpapers.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "wallpaper_id", name="uq_like_user_wallpaper"),)

    user = relationship("User")
    wallpaper = relationship("Wallpaper", back_populates="liked_by")


class WebhookConfig(Base):
    __tablename__ = "webhook_config"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StorageConfig(Base):
    __tablename__ = "storage_config"

    id = Column(Integer, primary_key=True)
    provider = Column(String(20), default="local")  # local | aliyun_oss
    bucket = Column(String(100), nullable=True)
    endpoint = Column(String(200), nullable=True)
    region = Column(String(50), nullable=True)
    access_key = Column(String(200), nullable=True)
    secret_key = Column(String(200), nullable=True)
    cdn_domain = Column(String(200), nullable=True)
    path_prefix = Column(String(100), nullable=True, default="wallpapers/")
    signed_url = Column(Boolean, default=False)
    enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SmtpConfig(Base):
    __tablename__ = "smtp_config"

    id = Column(Integer, primary_key=True)
    host = Column(String(200), nullable=True)
    port = Column(Integer, default=465)
    user = Column(String(200), nullable=True)
    password = Column(String(200), nullable=True)
    use_tls = Column(Boolean, default=True)
    from_addr = Column(String(200), nullable=True)
    from_name = Column(String(100), nullable=True, default="多点壁纸")
    enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SmsConfig(Base):
    __tablename__ = "sms_config"

    id = Column(Integer, primary_key=True)
    provider = Column(String(20), default="aliyun")  # aliyun | yunpian
    # 阿里云
    aliyun_access_key_id = Column(String(200), nullable=True)
    aliyun_access_key_secret = Column(String(200), nullable=True)
    aliyun_sign_name = Column(String(100), nullable=True)
    aliyun_template_code = Column(String(100), nullable=True)
    # 云片
    yunpian_api_key = Column(String(200), nullable=True)
    enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


class DebugConfig(Base):
    """调试日志开关（单例记录，id=1）"""
    __tablename__ = "debug_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    log_retention_days = Column(Integer, default=7)  # 日志保留天数
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DebugLog(Base):
    """调试日志：记录 App 的每一次 API 请求"""
    __tablename__ = "debug_logs"
    __table_args__ = (
        Index("ix_debug_logs_created_at", "created_at"),
        Index("ix_debug_logs_user_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, default=None)
    username = Column(String(50), nullable=True, default=None)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    query_string = Column(String(1000), nullable=True)
    request_body = Column(Text, nullable=True)        # 截断至 4KB
    response_status = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)     # 毫秒
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class SiteConfig(Base):
    """站点全局配置（单例记录，id=1）"""
    __tablename__ = "site_config"

    id = Column(Integer, primary_key=True)
    upload_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class WallpaperCategory(Base):
    """Junction table: wallpaper many-to-many category"""
    __tablename__ = "wallpaper_categories"
    __table_args__ = (
        UniqueConstraint("wallpaper_id", "category_id", name="uq_wallpaper_category"),
    )

    id = Column(Integer, primary_key=True, index=True)
    wallpaper_id = Column(Integer, ForeignKey("wallpapers.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    wallpaper = relationship("Wallpaper", back_populates="categories")
    category = relationship("Category", back_populates="wallpapers")
