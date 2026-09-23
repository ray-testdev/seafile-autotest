"""账号管理接口。"""
from api.client import BaseApi


class AccountApi(BaseApi):

    def admin_create_account(self, email, password, is_staff=None, is_active=None):
        """PUT /api2/accounts/{email}/

        新建账号成功返回 201，新建账号已存在返回 200
        """
        data = {"password": password}
        if is_staff is not None:
            data["is_staff"] = str(is_staff).lower()
        if is_active is not None:
            data["is_active"] = str(is_active).lower()
        return self.client.request("PUT", f"api2/accounts/{email}/", data=data)

    def get_account_info(self):
        """GET /api2/account/info/ —— 返回当前 Token 对应的账号信息。"""
        return self.client.request("GET", "api2/account/info/")

    def admin_delete_account(self, email):
        """DELETE /api2/accounts/{email}/ —— 仅管理员可调用。"""
        return self.client.request("DELETE", f"api2/accounts/{email}/")
