"""Shared webhook helpers for admin and user-facing flows."""
import threading
import httpx
import os
from sqlalchemy.orm import Session
from backend.models import WebhookConfig
from backend.config import get_settings

settings = get_settings()


def _build_notice(event: str, data: dict):
    """Build (title, content) for unipush-style webhooks."""
    if event == "wallpaper_uploaded":
        return "📤 新投稿待审核", (
            "标题：%s\nID：%s\n用户：%s\n请前往管理后台审核"
            % (data.get('title', '-'), data.get('id', '-'), data.get('username', '-')))
    if event == "wallpaper_reviewed":
        ok = bool(data.get("approved"))
        content = "标题：%s\nID：%s\n操作：%s" % (data.get('title', '-'), data.get('id', '-'), "通过" if ok else "拒绝")
        if data.get("reject_reason"):
            content += "\n原因：%s" % data.get("reject_reason")
        return ("✅ 壁纸审核通过" if ok else "❌ 壁纸被拒绝"), content
    if event in ("feedback_received", "admin_notification"):
        return "📬 通知", str(data.get("message", str(data)))[:500]
    return event, str(data)


def get_webhook_url(db: Session) -> str:
    cfg = db.query(WebhookConfig).filter(WebhookConfig.id == 1).first()
    return cfg.url if cfg else settings.WEBHOOK_URL or ""


def _send_wechat(url: str, content: str) -> dict:
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(url, json={"msgtype": "text", "text": {"content": content}})
        return {"ok": r.status_code == 200, "status_code": r.status_code, "text": r.text}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def send_webhook(db: Session, event: str, data: dict) -> dict:
    """
    Send a webhook notification.

    For WeChat Work bots the payload is adapted to a text message.
    For generic URLs the payload is a JSON object containing `event` and `data`.
    """
    url = get_webhook_url(db)
    if not url:
        return {"ok": False, "message": "Webhook URL not configured"}

    is_wechat = "qyapi.weixin.qq.com" in url
    if is_wechat:
        if event == "wallpaper_uploaded":
            content = (
                f"📤 新投稿待审核\\n"
                f"标题：{data.get('title', '-')}\\n"
                f"ID：{data.get('id', '-')}\\n"
                f"用户：{data.get('username', '-')}\\n"
                f"请前往管理后台审核"
            )
        elif event == "wallpaper_reviewed":
            action = "通过" if data.get("approved") else "拒绝"
            content = (
                f"✅ 壁纸审核结果\\n"
                f"标题：{data.get('title', '-')}\\n"
                f"ID：{data.get('id', '-')}\\n"
                f"操作：{action}"
            )
            if data.get("reject_reason"):
                content += f"\\n原因：{data.get('reject_reason')}"
        else:
            content = str(data)
        return _send_wechat(url, content)

    try:
        with httpx.Client(timeout=10) as client:
            title, content = _build_notice(event, data)
            r = client.post(url, json={"title": title, "content": content})
        return {"ok": r.status_code < 400, "status_code": r.status_code}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def send_webhook_async(db: Session, event: str, data: dict) -> None:
    """Query the webhook URL in the current thread, then send in a background thread."""
    url = get_webhook_url(db)
    if not url:
        return
    threading.Thread(target=_send_webhook_raw, args=(url, event, data), daemon=True).start()


def notify_admin(message: str) -> None:
    """Fire-and-forget admin notification via webhook (if configured)."""
    def _run():
        try:
            from backend.database import SessionLocal
            db = SessionLocal()
            try:
                send_webhook_async(db, "admin_notification", {"message": message})
            finally:
                db.close()
        except Exception as e:
            print(f"Notify admin error: {e}")
    threading.Thread(target=_run, daemon=True).start()


def _send_webhook_raw(url: str, event: str, data: dict) -> None:
    is_wechat = "qyapi.weixin.qq.com" in url
    if is_wechat:
        if event == "wallpaper_uploaded":
            content = (
                f"📤 新投稿待审核\\n"
                f"标题：{data.get('title', '-')}\\n"
                f"ID：{data.get('id', '-')}\\n"
                f"用户：{data.get('username', '-')}\\n"
                f"请前往管理后台审核"
            )
        elif event == "wallpaper_reviewed":
            action = "通过" if data.get("approved") else "拒绝"
            content = (
                f"✅ 壁纸审核结果\\n"
                f"标题：{data.get('title', '-')}\\n"
                f"ID：{data.get('id', '-')}\\n"
                f"操作：{action}"
            )
            if data.get("reject_reason"):
                content += f"\\n原因：{data.get('reject_reason')}"
        elif event == "feedback_received" or event == "admin_notification":
            msg = data.get("message", str(data))
            content = f"📬 通知\\n{msg[:500]}"
        else:
            content = str(data)
        _send_wechat(url, content)
        return

    try:
        with httpx.Client(timeout=10) as client:
            title, content = _build_notice(event, data)
            client.post(url, json={"title": title, "content": content})
    except Exception as e:
        print(f"Webhook async error: {e}")
