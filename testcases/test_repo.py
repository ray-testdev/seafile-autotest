"""03 资料库模块。"""
import allure
import pytest

from api.repo_api import RepoApi
from common.utils import unique_repo_name


@allure.feature("03_资料库模块")
class TestRepo:

    # ------------------------------------------------------------ 创建
    @allure.story("创建资料库")
    @allure.title("创建普通资料库成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_repo_success(self, shared_user_client):
        repo_api = RepoApi(shared_user_client)
        name = unique_repo_name()
        r = repo_api.create_repo(name)
        assert r.status_code == 200
        repo_id = r.json()["repo_id"]
        # 创建成功不能只看状态码：回查一次，确认库里真的是这个名字、且未加密
        info = repo_api.get_repo_info(repo_id).json()
        assert info["name"] == name
        assert info["encrypted"] is False
        assert info["permission"] == "rw"
        repo_api.delete_repo(repo_id)

    @allure.story("创建资料库")
    @allure.title("资料库名称为空返回 400")
    def test_create_repo_empty_name(self, shared_user_client):
        r = RepoApi(shared_user_client).create_repo("")
        assert r.status_code == 400
        assert r.json()["error_msg"] == "Library name is required."

    @allure.story("创建资料库")
    @allure.title("创建加密资料库成功")
    def test_create_encrypted_repo_success(self, shared_user_client):
        repo_api = RepoApi(shared_user_client)
        r = repo_api.create_encrypted_repo(unique_repo_name(), "abC123456")
        assert r.status_code == 200
        repo_id = r.json()["repo_id"]
        assert repo_api.get_repo_info(repo_id).json()["encrypted"] is True
        repo_api.delete_repo(repo_id)

    # ------------------------------------------------------------ 密码校验
    @allure.story("校验加密资料库密码")
    @allure.title("密码正确返回 200")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_verify_encrypted_repo_correct_password(self, shared_user_client, encrypted_repo):
        r = RepoApi(shared_user_client).verify_repo_password(encrypted_repo["id"], encrypted_repo["password"])
        assert r.status_code == 200
        assert r.json() == "success"

    @allure.story("校验加密资料库密码")
    @allure.title("密码错误返回 400")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_verify_encrypted_repo_wrong_password(self, shared_user_client, encrypted_repo):
        """密码错误时应返回 400，而不是笼统的失败。"""
        r = RepoApi(shared_user_client).verify_repo_password(encrypted_repo["id"], "definitely_wrong")
        assert r.status_code == 400
        assert r.json()["error_msg"] == "Incorrect password"

    @allure.story("校验加密资料库密码")
    @allure.title("资料库 ID 不存在返回 404")
    def test_verify_repo_bad_repo_id(self, shared_user_client, encrypted_repo):
        r = RepoApi(shared_user_client).verify_repo_password(encrypted_repo["id"] + "1", encrypted_repo["password"])
        assert r.status_code == 404

    @allure.story("校验加密资料库密码")
    @allure.title("访问他人资料库被拒绝 403")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_verify_other_account_repo_forbidden(self, shared_user_client, member_client, encrypted_repo):
        """水平越权：拿别人的 repo_id 去校验密码，必须是 403。"""
        r = RepoApi(member_client).verify_repo_password(encrypted_repo["id"], encrypted_repo["password"])
        assert r.status_code == 403
        assert r.json()["error_msg"] == "You do not have permission to access this library."

    # ------------------------------------------------------------ 查询
    @allure.story("获取资料库列表")
    @allure.title("列表包含刚创建的资料库")
    def test_get_repo_list_contains_created_repo(self, shared_user_client, repo):
        """列表接口里资料库的主键字段叫 id，不是创建接口返回的 repo_id。"""
        r = RepoApi(shared_user_client).get_repo_list()
        assert r.status_code == 200
        ids = [item["id"] for item in r.json()]
        assert repo["id"] in ids, "新建的资料库没有出现在列表中"
        names = {item["id"]: item["name"] for item in r.json()}
        assert names[repo["id"]] == repo["name"]

    @allure.story("获取资料库详情")
    @allure.title("获取指定资料库详情成功")
    def test_get_repo_info_success(self, shared_user_client, repo):
        r = RepoApi(shared_user_client).get_repo_info(repo["id"])
        assert r.status_code == 200
        assert r.json()["name"] == repo["name"]

    @allure.story("获取资料库详情")
    @allure.title("资料库 ID 不存在返回 404")
    def test_get_repo_info_bad_id(self, shared_user_client, repo):
        r = RepoApi(shared_user_client).get_repo_info(repo["id"] + "1")
        assert r.status_code == 404

    # ------------------------------------------------------------ 修改 / 删除
    @allure.story("重命名资料库")
    @allure.title("重命名资料库成功")
    def test_rename_repo_success(self, shared_user_client, repo):
        repo_api = RepoApi(shared_user_client)
        new_name = repo["name"] + "_renamed"
        r = repo_api.rename_repo(repo["id"], new_name)
        assert r.status_code == 200
        # 重命名必须回查确认生效，否则"接口返回 200 但名字没变"这类缺陷会漏掉
        assert repo_api.get_repo_info(repo["id"]).json()["name"] == new_name

    @allure.story("重命名资料库")
    @allure.title("重命名为空字符串（疑似服务端缺陷，已记录）")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.defect
    def test_rename_repo_to_empty_name(self, shared_user_client, repo):
        """创建接口拒绝空名称（400），重命名接口却接受空名称（200），两个接口校验不一致。

        本条用例锁定"当前实际行为"，用于回归：一旦服务端修复（改为 400），
        这条用例会失败，提醒我们去更新断言并关闭缺陷。
        """
        repo_api = RepoApi(shared_user_client)
        r = repo_api.rename_repo(repo["id"], "")
        assert r.status_code == 200, "服务端行为已变化，请复核缺陷单"
        # 空名称确实被写进去了
        assert repo_api.get_repo_info(repo["id"]).json()["name"] == ""

    @allure.story("删除资料库")
    @allure.title("删除资料库成功且确实查不到了")
    def test_delete_repo_success(self, shared_user_client):
        repo_api = RepoApi(shared_user_client)
        repo_id = repo_api.create_repo(unique_repo_name()).json()["repo_id"]
        r = repo_api.delete_repo(repo_id)
        assert r.status_code == 200
        # 删除类用例最容易只断言 200 就收工，必须回查确认资源真的没了
        assert repo_api.get_repo_info(repo_id).status_code == 404
