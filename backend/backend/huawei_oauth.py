import os
from typing import Optional

import httpx

from backend.config import get_settings

settings = get_settings()

HUAWEI_TOKEN_URL = "https://oauth-login.cloud.huawei.com/oauth2/v3/token"
HUAWEI_USERINFO_URL = "https://api.cloud.huawei.com/rest.php?nsp_ts=%s&nsp_svc=G.OpenUser.getInfo"


def huawei_get_user_info(access_token: str) -> Optional[dict]:
    """Fetch Huawei user info using access token."""
    if not settings.HUAWEI_CLIENT_ID:
        return None

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"appid": settings.HUAWEI_CLIENT_ID, "client_id": settings.HUAWEI_CLIENT_ID}

    try:
        response = httpx.get(HUAWEI_USERINFO_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("ret") == 0:
            return data
        return None
    except Exception as e:
        print(f"⚠️ Huawei login failed: {e}")
        return None
