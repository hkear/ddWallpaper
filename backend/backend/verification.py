from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.models import VerificationCode, AuthConfig, SmtpConfig, SmsConfig
from backend.config import get_settings
from backend.email import send_email_code, generate_code
from backend.sms import send_sms_code

settings = get_settings()

CODE_EXPIRE_MINUTES = 10


def get_auth_config(db: Session) -> AuthConfig:
    """Get or create the singleton AuthConfig row."""
    config = db.query(AuthConfig).first()
    if not config:
        config = AuthConfig(
            enable_email_verify=settings.REGISTER_ENABLE_EMAIL_VERIFY,
            enable_sms_verify=settings.REGISTER_ENABLE_SMS_VERIFY,
            require_email=settings.REGISTER_REQUIRE_EMAIL,
            email_provider="smtp",
            sms_provider=settings.SMS_PROVIDER,
            enable_huawei_login=False,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def get_smtp_credentials(db: Session) -> dict:
    """Resolve SMTP credentials: enabled DB SmtpConfig > env vars."""
    cfg = db.query(SmtpConfig).first()
    if cfg and cfg.enabled and cfg.host and cfg.user and cfg.password:
        return {
            "host": cfg.host,
            "port": cfg.port,
            "user": cfg.user,
            "password": cfg.password,
            "from_addr": cfg.from_addr or cfg.user,
            "from_name": cfg.from_name or "多点壁纸",
        }
    return {
        "host": settings.EMAIL_SMTP_HOST,
        "port": settings.EMAIL_SMTP_PORT,
        "user": settings.EMAIL_SMTP_USER,
        "password": settings.EMAIL_SMTP_PASSWORD,
        "from_addr": settings.EMAIL_FROM or settings.EMAIL_SMTP_USER,
        "from_name": settings.EMAIL_FROM_NAME,
    }


def get_sms_credentials(db: Session) -> dict:
    """Resolve SMS credentials: enabled DB SmsConfig > env vars."""
    cfg = db.query(SmsConfig).first()
    if cfg and cfg.enabled:
        if cfg.provider == "aliyun" and cfg.aliyun_access_key_id and cfg.aliyun_access_key_secret:
            return {
                "provider": "aliyun",
                "access_key_id": cfg.aliyun_access_key_id,
                "access_key_secret": cfg.aliyun_access_key_secret,
                "sign_name": cfg.aliyun_sign_name,
                "template_code": cfg.aliyun_template_code,
            }
        if cfg.provider == "yunpian" and cfg.yunpian_api_key:
            return {"provider": "yunpian", "api_key": cfg.yunpian_api_key}
    return {
        "provider": settings.SMS_PROVIDER,
        "access_key_id": settings.ALIYUN_ACCESS_KEY_ID,
        "access_key_secret": settings.ALIYUN_ACCESS_KEY_SECRET,
        "sign_name": settings.ALIYUN_SMS_SIGN_NAME,
        "template_code": settings.ALIYUN_SMS_TEMPLATE_CODE,
        "api_key": settings.YUNPIAN_API_KEY,
    }


def create_verification_code(db: Session, target: str, code_type: str) -> str:
    """Create and save a new verification code, invalidating old ones."""
    # Mark previous codes as used
    db.query(VerificationCode).filter(
        VerificationCode.target == target,
        VerificationCode.code_type == code_type,
        VerificationCode.used == False,
    ).update({"used": True})

    code = generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=CODE_EXPIRE_MINUTES)
    record = VerificationCode(
        target=target,
        code_type=code_type,
        code=code,
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()
    return code


def verify_code(db: Session, target: str, code_type: str, code: Optional[str]) -> bool:
    """Verify a code and mark it used."""
    if not code:
        return False
    now = datetime.now(timezone.utc)
    record = db.query(VerificationCode).filter(
        VerificationCode.target == target,
        VerificationCode.code_type == code_type,
        VerificationCode.code == code,
        VerificationCode.used == False,
        VerificationCode.expires_at > now,
    ).first()
    if not record:
        return False
    record.used = True
    db.commit()
    return True


def send_verification_code(db: Session, target: str, code_type: str) -> tuple[str, bool]:
    """Generate and send verification code. Returns (code, success)."""
    code = create_verification_code(db, target, code_type)
    config = get_auth_config(db)

    if code_type == "email":
        ok = send_email_code(target, code, cfg=get_smtp_credentials(db))
    elif code_type == "sms":
        sms_cfg = get_sms_credentials(db)
        provider = config.sms_provider or sms_cfg.get("provider", "aliyun")
        ok = send_sms_code(target, code, provider=provider, cfg=sms_cfg)
    else:
        ok = False

    return code, ok
