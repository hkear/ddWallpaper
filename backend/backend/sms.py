import os
import json
from typing import Optional

import requests
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


def _send_aliyun_sms(phone: str, code: str, cfg: Optional[dict] = None) -> bool:
    cfg = cfg or {}
    access_key_id = cfg.get("access_key_id") or os.getenv("ALIYUN_ACCESS_KEY_ID")
    access_key_secret = cfg.get("access_key_secret") or os.getenv("ALIYUN_ACCESS_KEY_SECRET")
    sign_name = cfg.get("sign_name") or os.getenv("ALIYUN_SMS_SIGN_NAME")
    template_code = cfg.get("template_code") or os.getenv("ALIYUN_SMS_TEMPLATE_CODE")

    if not all([access_key_id, access_key_secret, sign_name, template_code]):
        print("⚠️ Aliyun SMS not fully configured")
        return False

    client = AcsClient(access_key_id, access_key_secret, "cn-hangzhou")
    request = CommonRequest()
    request.set_accept_format("json")
    request.set_domain("dysmsapi.aliyuncs.com")
    request.set_method("POST")
    request.set_protocol_type("https")
    request.set_version("2017-05-25")
    request.set_action_name("SendSms")
    request.add_query_param("PhoneNumbers", phone)
    request.add_query_param("SignName", sign_name)
    request.add_query_param("TemplateCode", template_code)
    request.add_query_param("TemplateParam", json.dumps({"code": code}))

    try:
        response = client.do_action_with_exception(request)
        resp_obj = json.loads(response)
        return resp_obj.get("Code") == "OK"
    except Exception as e:
        print(f"⚠️ Aliyun SMS failed for {phone}: {e}")
        return False


def _send_yunpian_sms(phone: str, code: str, cfg: Optional[dict] = None) -> bool:
    cfg = cfg or {}
    api_key = cfg.get("api_key") or os.getenv("YUNPIAN_API_KEY")
    if not api_key:
        print("⚠️ YunPian API key not configured")
        return False

    url = "https://sms.yunpian.com/v2/sms/single_send.json"
    text = f"【多点壁纸】您的验证码是{code}。如非本人操作，请忽略本短信。"
    payload = {"apikey": api_key, "mobile": phone, "text": text}

    try:
        response = requests.post(url, data=payload, timeout=10)
        resp_obj = response.json()
        return resp_obj.get("code") == 0
    except Exception as e:
        print(f"⚠️ YunPian SMS failed for {phone}: {e}")
        return False


def send_sms_code(phone: str, code: str, provider: Optional[str] = None, cfg: Optional[dict] = None) -> bool:
    """Send verification code via SMS."""
    provider = (provider or os.getenv("SMS_PROVIDER", "aliyun")).lower()
    if provider == "aliyun":
        return _send_aliyun_sms(phone, code, cfg)
    elif provider == "yunpian":
        return _send_yunpian_sms(phone, code, cfg)
    else:
        print(f"⚠️ Unknown SMS provider: {provider}")
        return False
