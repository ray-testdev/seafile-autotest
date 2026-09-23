"""02 账号模块。"""
import allure

from api.account_api import AccountApi
from api.client import SeafileClient
from common.config import BASE_URL, TEST_PASSWORD
from common.utils import unique_email


@allure.feature("02_账号模块")
class TestAccount:

    @allure.story("创建账号")
    @allure.title("管理员创建新账号成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_account_success(self, admin_client):
        account_api = AccountApi(admin_client)
        email = unique_email()
        r = account_api.admin_create_account(email, TEST_PASSWORD)
        assert r.status_code == 201
        # 断言响应体，而不只是状态码
        body = r.json()
        assert body["email"] == email
        assert body["is_active"] is True
        account_api.admin_delete_account(email)

    @allure.story("创建账号")
    @allure.title("对已存在账号再次创建，走更新逻辑返回 200")
    def test_create_existing_account_returns_200(self, admin_client):
        """同一个接口"新建返回 201、已存在返回 200"——这是接口约定，必须锁住。"""
        account_api = AccountApi(admin_client)
        email = unique_email()
        assert account_api.admin_create_account(email, TEST_PASSWORD).status_code == 201
        r = account_api.admin_create_account(email, TEST_PASSWORD)
        assert r.status_code == 200
        account_api.admin_delete_account(email)

    @allure.story("创建账号")
    @allure.title("普通成员创建账号被拒绝 403")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_account_as_member_forbidden(self, member_client):
        account_api = AccountApi(member_client)
        r = account_api.admin_create_account(unique_email(), TEST_PASSWORD)
        assert r.status_code == 403

    @allure.story("获取账号信息")
    @allure.title("获取当前账号信息成功")
    def test_get_account_info_success(self, admin_client):
        r = AccountApi(admin_client).get_account_info()
        assert r.status_code == 200
        body = r.json()
        assert body["is_staff"] is True, "管理员账号的 is_staff 应为 true"
        assert body["name"], "账号信息缺少 name 字段"

    @allure.story("获取账号信息")
    @allure.title("Token 非法返回 401")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_account_info_invalid_token(self, bad_token_client):
        """401 = 你给的凭证是错的。"""
        r = AccountApi(bad_token_client).get_account_info()
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid token"

    @allure.story("获取账号信息")
    @allure.title("Token 含空格时返回 401，提示文案与 Token 不存在不同")
    def test_get_account_info_malformed_token(self):
        """Token 里带空格 → 服务端判定为"请求头格式错误"，
        提示是 "Token string should not contain spaces."；这与
        "格式合法但服务端不认识"返回的 "Invalid token" 不是同一条分支。

        这也是 bad_token_client 要用"真实 Token + 1 个字符"构造的原因：
        随手写的字符串（尤其含空格的）会测到另一条分支上去。
        """
        client = SeafileClient(BASE_URL, token="wrong token")
        r = AccountApi(client).get_account_info()
        assert r.status_code == 401
        assert "should not contain spaces" in r.json()["detail"]
        client.close()

    @allure.story("获取账号信息")
    @allure.title("完全不带 Token 返回 403")
    def test_get_account_info_without_token(self, anonymous_client):
        """403 = 你没提供凭证。401 与 403 的语义区别是接口测试常见考点。"""
        r = AccountApi(anonymous_client).get_account_info()
        assert r.status_code == 403
        assert r.json()["detail"] == "Authentication credentials were not provided."

    @allure.story("删除账号")
    @allure.title("管理员删除账号成功")
    def test_delete_account_success(self, admin_client):
        account_api = AccountApi(admin_client)
        email = unique_email()
        account_api.admin_create_account(email, TEST_PASSWORD)
        r = account_api.admin_delete_account(email)
        assert r.status_code == 200
        assert r.json()["success"] is True

    @allure.story("删除账号")
    @allure.title("删除不存在的账号返回 202")
    def test_delete_nonexistent_account(self, admin_client):
        """202 = 服务端接受请求，但目标本来就不存在。"""
        r = AccountApi(admin_client).admin_delete_account(unique_email())
        assert r.status_code == 202

    @allure.story("删除账号")
    @allure.title("普通成员删除账号被拒绝 403")
    def test_delete_account_as_member_forbidden(self, admin_client, member_client):
        email = unique_email()
        AccountApi(admin_client).admin_create_account(email, TEST_PASSWORD)
        r = AccountApi(member_client).admin_delete_account(email)
        assert r.status_code == 403
        # 越权失败后，账号必须仍然存在 —— 只断言 403 是不够的
        assert AccountApi(admin_client).admin_create_account(email, TEST_PASSWORD).status_code == 200
        AccountApi(admin_client).admin_delete_account(email)
