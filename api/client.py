"""底层 HTTP 客户端：拼 URL、带 Token、发请求。

这一层不认识具体业务接口，业务语义都在 api/ 下的几个 Api 类里。
"""
import re
import time

import requests

from common.config import REQUEST_TIMEOUT

# 被限流时最多重试 3 次，单次最多等 10 秒
THROTTLE_MAX_RETRIES = 3
THROTTLE_MAX_WAIT = 10.0

_WAIT_RE = re.compile(r"available in ([0-9.]+) second")


class SeafileClient:
    """一个实例代表一个登录身份。"""

    def __init__(self, base_url, token=None, timeout=REQUEST_TIMEOUT):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.token = token
        self.session = requests.Session()

    def set_token(self, token):
        self.token = token

    @property
    def headers(self):
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        return headers

    def request(self, method, path, **kwargs):
        # path 可能是相对路径，也可能是服务端返回的完整 URL（上传链接、下载链接）
        if path.startswith(("http://", "https://")):
            url = path
        else:
            url = f"{self.base_url}{path.lstrip('/')}"

        kwargs.setdefault("timeout", self.timeout)

        # Seafile 的登录接口有频率限制。被限流后拿不到 token，后续请求会全部
        # 变成 403 "credentials were not provided"，报错完全指不到真正原因，
        # 所以这里按服务端提示的等待时长重试，避免一次限流打挂整个套件。
        for attempt in range(THROTTLE_MAX_RETRIES + 1):
            resp = self.session.request(method, url, headers=self.headers, **kwargs)
            if resp.status_code != 429 or attempt == THROTTLE_MAX_RETRIES:
                return resp
            time.sleep(min(self._suggested_wait(resp), THROTTLE_MAX_WAIT))
        return resp

    @staticmethod
    def _suggested_wait(resp):
        # 响应形如 {"detail": "Request was throttled. Expected available in 29.0 seconds."}
        try:
            detail = resp.json().get("detail", "")
        except ValueError:
            detail = ""
        m = _WAIT_RE.search(detail)
        return float(m.group(1)) if m else 1.0

    def close(self):
        self.session.close()


class BaseApi:
    """各业务接口类的基类，统一持有 client。"""

    def __init__(self, client: SeafileClient):
        self.client = client
