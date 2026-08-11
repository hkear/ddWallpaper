import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "mysql")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "wallpaper")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "wallpaper123")
    DB_NAME: str = os.getenv("DB_NAME", "wallpaper_db")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-abc123xyz")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Upload
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB

    # Webhook
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")

    # CORS (set via CORS_ORIGINS env var, comma-separated)
    CORS_ORIGINS: list[str] = ["https://api.ddbz.art", "https://ddbz.art", "https://www.ddbz.art", "https://pc.ddbz.art", "https://api.ddbz.cn", "https://ddbz.cn", "https://www.ddbz.cn", "https://app.ddbz.cn", "https://wallpaper.ddbz.cn"]

    # Debug / security toggles
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    ENABLE_API_DOCS: bool = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"
    ENABLE_HEALTH_CHECK: bool = os.getenv("ENABLE_HEALTH_CHECK", "false").lower() == "true"

    # Auth verification toggles (can be overridden by DB AuthConfig at runtime)
    REGISTER_REQUIRE_EMAIL: bool = os.getenv("REGISTER_REQUIRE_EMAIL", "true").lower() == "true"
    REGISTER_ENABLE_EMAIL_VERIFY: bool = os.getenv("REGISTER_ENABLE_EMAIL_VERIFY", "false").lower() == "true"
    REGISTER_ENABLE_SMS_VERIFY: bool = os.getenv("REGISTER_ENABLE_SMS_VERIFY", "false").lower() == "true"
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "aliyun")

    # Huawei OAuth (reserved for one-click login)
    HUAWEI_CLIENT_ID: str = os.getenv("HUAWEI_CLIENT_ID", "")
    HUAWEI_CLIENT_SECRET: str = os.getenv("HUAWEI_CLIENT_SECRET", "")

    # Aliyun OSS (env defaults; can be overridden by DB StorageConfig)
    OSS_ENABLED: bool = os.getenv("OSS_ENABLED", "false").lower() == "true"
    OSS_BUCKET: str = os.getenv("OSS_BUCKET", "")
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "")
    OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID", "")
    OSS_ACCESS_KEY_SECRET: str = os.getenv("OSS_ACCESS_KEY_SECRET", "")
    OSS_CDN_DOMAIN: str = os.getenv("OSS_CDN_DOMAIN", "")
    OSS_PATH_PREFIX: str = os.getenv("OSS_PATH_PREFIX", "wallpapers/")
    OSS_SIGNED_URL: bool = os.getenv("OSS_SIGNED_URL", "false").lower() == "true"

    # SMTP (env defaults; can be overridden by DB SmtpConfig)
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "465"))
    EMAIL_SMTP_USER: str = os.getenv("EMAIL_SMTP_USER", "")
    EMAIL_SMTP_PASSWORD: str = os.getenv("EMAIL_SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "多点壁纸")

    # Aliyun SMS (env defaults; can be overridden by DB SmsConfig)
    ALIYUN_ACCESS_KEY_ID: str = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    ALIYUN_ACCESS_KEY_SECRET: str = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    ALIYUN_SMS_SIGN_NAME: str = os.getenv("ALIYUN_SMS_SIGN_NAME", "")
    ALIYUN_SMS_TEMPLATE_CODE: str = os.getenv("ALIYUN_SMS_TEMPLATE_CODE", "")
    YUNPIAN_API_KEY: str = os.getenv("YUNPIAN_API_KEY", "")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
