"""Storage abstraction layer: local filesystem / Aliyun OSS.

The active backend is resolved from the StorageConfig DB row (singleton id=1)
with environment variables as fallback when the row does not exist or is
incomplete.
"""
import os
import shutil
import logging

from backend.config import get_settings

logger = logging.getLogger(__name__)


class BaseStorage:
    """Storage backend interface."""

    def save(self, local_path: str, key: str) -> str:
        """Persist the local file under `key` and return its public URL."""
        raise NotImplementedError

    def url(self, key: str) -> str:
        """Return the public URL for an object stored under `key`."""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """Delete the object stored under `key`."""
        raise NotImplementedError


class LocalStorage(BaseStorage):
    """Local filesystem storage backed by UPLOAD_DIR + /static mount."""

    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = self.settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def save(self, local_path: str, key: str) -> str:
        dest = os.path.join(self.upload_dir, key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.abspath(local_path) != os.path.abspath(dest):
            shutil.move(local_path, dest)
        return self.url(key)

    def url(self, key: str) -> str:
        return f"/static/{key}"

    def delete(self, key: str) -> bool:
        path = os.path.join(self.upload_dir, key)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False


class AliyunOSSStorage(BaseStorage):
    """Aliyun OSS storage."""

    def __init__(self, access_key: str, secret_key: str, endpoint: str,
                 bucket: str, cdn_domain: str = "", path_prefix: str = "wallpapers/",
                 signed_url: bool = False):
        import oss2
        self.auth = oss2.Auth(access_key, secret_key)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket)
        self.endpoint = endpoint
        self.bucket_name = bucket
        self.cdn_domain = (cdn_domain or "").rstrip("/")
        self.path_prefix = path_prefix or ""
        self.signed_url = signed_url
        self.settings = get_settings()

    def _object_key(self, key: str) -> str:
        return f"{self.path_prefix}{key}" if self.path_prefix else key

    def save(self, local_path: str, key: str) -> str:
        object_key = self._object_key(key)
        with open(local_path, "rb") as f:
            self.bucket.put_object(object_key, f)
        try:
            os.remove(local_path)
        except OSError:
            pass
        return self.url(key)

    def url(self, key: str) -> str:
        object_key = self._object_key(key)
        if self.signed_url:
            # 私有 bucket 使用签名 URL，有效期 7 天
            return self.bucket.sign_url("GET", object_key, 7 * 24 * 3600)
        if self.cdn_domain:
            return f"https://{self.cdn_domain}/{object_key}"
        endpoint_host = self.endpoint.replace("https://", "").replace("http://", "")
        return f"https://{self.bucket_name}.{endpoint_host}/{object_key}"

    def delete(self, key: str) -> bool:
        try:
            self.bucket.delete_object(self._object_key(key))
            return True
        except Exception as e:
            logger.warning(f"OSS delete failed for {key}: {e}")
            return False


_local_storage: BaseStorage = None


def get_storage(db=None) -> BaseStorage:
    """Resolve the active storage backend.

    Priority: enabled DB StorageConfig > env OSS_ENABLED > local storage.
    """
    global _local_storage
    settings = get_settings()

    if db is not None:
        try:
            from backend.models import StorageConfig
            cfg = db.query(StorageConfig).order_by(StorageConfig.id).first()
            if cfg and cfg.enabled and cfg.provider == "aliyun_oss":
                if cfg.access_key and cfg.secret_key and cfg.endpoint and cfg.bucket:
                    return AliyunOSSStorage(
                        access_key=cfg.access_key,
                        secret_key=cfg.secret_key,
                        endpoint=cfg.endpoint,
                        bucket=cfg.bucket,
                        cdn_domain=cfg.cdn_domain or "",
                        path_prefix=cfg.path_prefix or "wallpapers/",
                        signed_url=cfg.signed_url or False,
                    )
                logger.warning("StorageConfig enabled but OSS credentials incomplete; falling back to local")
        except Exception as e:
            logger.warning(f"Failed to read StorageConfig, using env/local: {e}")

    if settings.OSS_ENABLED and settings.OSS_ACCESS_KEY_ID and settings.OSS_ACCESS_KEY_SECRET \
            and settings.OSS_ENDPOINT and settings.OSS_BUCKET:
        try:
            return AliyunOSSStorage(
                access_key=settings.OSS_ACCESS_KEY_ID,
                secret_key=settings.OSS_ACCESS_KEY_SECRET,
                endpoint=settings.OSS_ENDPOINT,
                bucket=settings.OSS_BUCKET,
                cdn_domain=settings.OSS_CDN_DOMAIN,
                path_prefix=settings.OSS_PATH_PREFIX,
                signed_url=getattr(settings, 'OSS_SIGNED_URL', False),
            )
        except Exception as e:
            logger.warning(f"Failed to init OSS storage from env, using local: {e}")

    if _local_storage is None:
        _local_storage = LocalStorage()
    return _local_storage
