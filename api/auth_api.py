"""认证接口。"""
from api.client import BaseApi

# 同一套"地址 + 账号 + 密码"在一次会话里只真正登录一次。
# Seafile 的 /api2/auth-token/ 有频率限制，每条用例都登录会把限流打满。
_TOKEN_CACHE = {}


class AuthApi(BaseApi):

    def login(self, username, password, use_cache=True):
        """POST /api2/auth-token/

        成功 200 并返回 token；账号或密码错误、字段为空都返回 400。
        """
        cache_key = (self.client.base_url, username, password)
        if use_cache and cache_key in _TOKEN_CACHE:
            cached = _TOKEN_CACHE[cache_key]
            self.client.set_token(cached.json()["token"])
            return cached

        data = {"username": username, "password": password}
        r = self.client.request("POST", "api2/auth-token/", data=data)
        if r.status_code == 200:
            self.client.set_token(r.json()["token"])
            _TOKEN_CACHE[cache_key] = r
        return r

    @staticmethod
    def clear_cache():
        _TOKEN_CACHE.clear()
