"""资料库接口。"""
from api.client import BaseApi


class RepoApi(BaseApi):

    def create_repo(self, repo_name):
        """POST /api2/repos/ —— 创建普通资料库，成功 200，返回体含 repo_id。"""
        return self.client.request("POST", "api2/repos/", data={"name": repo_name})

    def create_encrypted_repo(self, repo_name, password):
        """POST /api2/repos/ —— 带 passwd 参数即创建加密资料库。"""
        data = {"name": repo_name, "passwd": password}
        return self.client.request("POST", "api2/repos/", data=data)

    def verify_repo_password(self, repo_id, password):
        """POST /api2/repos/{repo_id}/ —— 校验加密资料库密码。

        正确 200；密码错误 400；repo_id 不存在 404；无权访问 403。
        """
        return self.client.request("POST", f"api2/repos/{repo_id}/", data={"password": password})

    def get_repo_list(self, repo_type=None):
        """GET /api2/repos/ —— 列出当前账号的资料库。

        注意：列表里的主键字段叫 id，而创建接口返回的叫 repo_id，两者不一致，
        写断言时不要想当然（本项目有专门用例覆盖这一点）。
        """
        params = {}
        if repo_type is not None:
            params["type"] = repo_type
        return self.client.request("GET", "api2/repos/", params=params)

    def get_repo_info(self, repo_id):
        """GET /api2/repos/{repo_id}/ —— 资料库详情，含 encrypted 标志。"""
        return self.client.request("GET", f"api2/repos/{repo_id}/")

    def rename_repo(self, repo_id, new_name, op="rename"):
        """POST /api2/repos/{repo_id}/?op=rename"""
        return self.client.request(
            "POST", f"api2/repos/{repo_id}/", data={"repo_name": new_name}, params={"op": op}
        )

    def delete_repo(self, repo_id):
        """DELETE /api2/repos/{repo_id}/"""
        return self.client.request("DELETE", f"api2/repos/{repo_id}/")
