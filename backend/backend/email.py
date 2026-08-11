import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.config import get_settings

settings = get_settings()


def generate_code(length: int = 6) -> str:
    """Generate a numeric verification code."""
    return ''.join(random.choices(string.digits, k=length))


def send_email_code(to_email: str, code: str, cfg: Optional[dict] = None) -> bool:
    """Send verification code via SMTP.

    `cfg` may contain host/port/user/password/from_addr/from_name resolved
    from the SmtpConfig DB row; falls back to environment variables.
    """
    cfg = cfg or {}
    smtp_host = cfg.get("host") or os.getenv("EMAIL_SMTP_HOST")
    smtp_port = int(cfg.get("port") or os.getenv("EMAIL_SMTP_PORT", "465"))
    smtp_user = cfg.get("user") or os.getenv("EMAIL_SMTP_USER")
    smtp_pass = cfg.get("password") or os.getenv("EMAIL_SMTP_PASSWORD")
    from_addr = cfg.get("from_addr") or os.getenv("EMAIL_FROM", smtp_user)
    from_name = cfg.get("from_name") or os.getenv("EMAIL_FROM_NAME", "多点壁纸")

    if not all([smtp_host, smtp_user, smtp_pass]):
        print("⚠️ Email SMTP not configured")
        return False

    subject = "【多点壁纸】验证码"
    body = f"您的验证码是：{code}\n验证码有效期为 10 分钟，请勿泄露给他人。"

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = formataddr((from_name, from_addr))
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port) if smtp_port == 465 else smtplib.SMTP(smtp_host, smtp_port)
        if smtp_port == 587:
            server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"⚠️ Failed to send email to {to_email}: {e}")
        return False
