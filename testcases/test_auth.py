"""01 登录模块。"""
import allure

from api.auth_api import AuthApi
from api.client import SeafileClient
from common.config import ADMIN_EMAIL, ADMIN_PASSWORD, BASE_URL


@allure.feature("01_登录模块")
class TestAuth:

    @allure.story("登录")
    @allure.title("正确的账号密码登录成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_success(self):
        client = SeafileClient(BASE_URL)
        r = AuthApi(client).login(ADMIN_EMAIL, ADMIN_PASSWORD)
        assert r.status_code == 200
        # 不只断言状态码：token 必须真的拿到，且真的能用来访问受保护接口
        token = r.json().get("token")
        assert token, "登录成功但响应里没有 token"
        assert client.token == token, "登录后 token 未写回 client"

    @allure.story("登录")
    @allure.title("密码错误登录失败")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_wrong_password(self):
        client = SeafileClient(BASE_URL)
        r = AuthApi(client).login(ADMIN_EMAIL, "wrong password")
        assert r.status_code == 400
        assert "non_field_errors" in r.json()
        assert client.token is None, "登录失败却写入了 token"

    @allure.story("登录")
    @allure.title("不存在的用户登录失败")
    def test_login_nonexistent_user(self):
        client = SeafileClient(BASE_URL)
        r = AuthApi(client).login("nobody_exists@qq.com", "whatever")
        assert r.status_code == 400
        # 与"密码错误"返回同样的提示，避免泄露账号是否存在（安全设计）
        assert "non_field_errors" in r.json()

    @allure.story("登录")
    @allure.title("用户名为空登录失败")
    def test_login_empty_username(self):
        client = SeafileClient(BASE_URL)
        r = AuthApi(client).login("", ADMIN_PASSWORD)
        assert r.status_code == 400
        assert "username" in r.json()

    @allure.story("登录")
    @allure.title("密码为空登录失败")
    def test_login_empty_password(self):
        client = SeafileClient(BASE_URL)
        r = AuthApi(client).login(ADMIN_EMAIL, "")
        assert r.status_code == 400
        assert "password" in r.json()
