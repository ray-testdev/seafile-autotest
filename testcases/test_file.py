"""04 文件模块。"""
import allure
import pytest

from api.file_api import FileApi
from common.config import REMOTE_FILE_PATH, UPLOAD_FILE, UPLOAD_FILE_NAME


@allure.feature("04_文件模块")
class TestFile:

    # ------------------------------------------------------------ 上传
    @allure.story("获取上传链接")
    @allure.title("获取上传链接成功")
    def test_get_upload_link_success(self, shared_user_client, repo):
        r = FileApi(shared_user_client).get_upload_link(repo["id"])
        assert r.status_code == 200
        # 响应体是 JSON 字符串，必须能直接当 URL 用（用 .text 会带上引号）
        link = r.json()
        assert isinstance(link, str) and link.startswith("http")

    @allure.story("上传文件")
    @allure.title("上传文件成功且文件信息正确")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_upload_file_success(self, shared_user_client, repo, uploaded_file):
        file_api = FileApi(shared_user_client)
        r = file_api.get_file_info(repo["id"], uploaded_file)
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == UPLOAD_FILE_NAME
        assert body["size"] == UPLOAD_FILE.stat().st_size, "服务端文件大小与本地上传文件不一致"

    @allure.story("上传文件")
    @allure.title("上传到他人资料库被拒绝 403")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_upload_to_other_account_repo_forbidden(self, shared_user_client, member_client, repo):
        r = FileApi(member_client).get_upload_link(repo["id"])
        assert r.status_code == 403

    # ------------------------------------------------------------ 下载
    @allure.story("获取下载链接")
    @allure.title("获取下载链接成功")
    def test_get_download_link_success(self, shared_user_client, repo, uploaded_file):
        r = FileApi(shared_user_client).get_download_link(repo["id"], uploaded_file)
        assert r.status_code == 200
        assert r.json().startswith("http")

    @allure.story("下载文件")
    @allure.title("下载文件内容与本地文件完全一致")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_download_file_content_matches(self, shared_user_client, repo, uploaded_file):
        """上传 -> 下载 -> 逐字节比对。

        只断言下载链接返回 200 是不够的：文件损坏或串档时状态码照样是 200。
        """
        file_api = FileApi(shared_user_client)
        download_link = file_api.get_download_link(repo["id"], uploaded_file).json()
        r = file_api.download_file(download_link)
        assert r.status_code == 200
        assert r.content == UPLOAD_FILE.read_bytes(), "下载内容与源文件不一致（文件损坏或串档）"

    @allure.story("获取下载链接")
    @allure.title("文件不存在返回 404")
    def test_get_download_link_nonexistent_file(self, shared_user_client, repo, uploaded_file):
        r = FileApi(shared_user_client).get_download_link(repo["id"], "/not_exist.txt")
        assert r.status_code == 404

    @allure.story("获取下载链接")
    @allure.title("文件路径为空返回 400")
    def test_get_download_link_empty_path(self, shared_user_client, repo):
        r = FileApi(shared_user_client).get_download_link(repo["id"], "")
        assert r.status_code == 400
        assert r.json()["error_msg"] == "Path is missing."

    @allure.story("获取文件信息")
    @allure.title("获取文件信息成功")
    def test_get_file_info_success(self, shared_user_client, repo, uploaded_file):
        r = FileApi(shared_user_client).get_file_info(repo["id"], uploaded_file)
        assert r.status_code == 200
        assert r.json()["name"] == UPLOAD_FILE_NAME

    @allure.story("获取文件信息")
    @allure.title("文件不存在返回 404")
    def test_get_file_info_nonexistent(self, shared_user_client, repo, uploaded_file):
        r = FileApi(shared_user_client).get_file_info(repo["id"], "/not_exist.txt")
        assert r.status_code == 404

    # ------------------------------------------------------------ 重命名
    @allure.story("重命名文件")
    @allure.title("重命名文件成功且新旧路径状态正确")
    def test_rename_file_success(self, shared_user_client, repo, uploaded_file):
        file_api = FileApi(shared_user_client)
        r = file_api.rename_file(repo["id"], uploaded_file, "renamed.txt", reloaddir="true")
        assert r.status_code == 200
        assert file_api.get_file_info(repo["id"], "/renamed.txt").status_code == 200
        assert file_api.get_file_info(repo["id"], uploaded_file).status_code == 404, "旧文件名仍然可访问"

    @allure.story("重命名文件")
    @allure.title("新文件名与原文件名相同返回 409")
    def test_rename_file_same_name(self, shared_user_client, repo, uploaded_file):
        r = FileApi(shared_user_client).rename_file(repo["id"], uploaded_file, UPLOAD_FILE_NAME, reloaddir="true")
        assert r.status_code == 409

    @allure.story("重命名文件")
    @allure.title("重命名不存在的文件（疑似服务端缺陷，已记录）")
    @pytest.mark.defect
    def test_rename_nonexistent_file(self, shared_user_client, repo):
        """文件不存在时返回 520（非标准状态码），而不是语义正确的 404。

        520 无法被通用 HTTP 客户端正确归类，自动化脚本也很难据此判断错误类型，
        已记录为疑似缺陷。本用例锁定当前行为用于回归。
        """
        r = FileApi(shared_user_client).rename_file(repo["id"], "/not_exist.txt", "zzz.txt", reloaddir="true")
        assert r.status_code == 520, "服务端行为已变化，请复核缺陷单"

    @allure.story("重命名文件")
    @allure.title("不传 reloaddir 时重命名已生效却返回 404（疑似服务端缺陷，已记录）")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.defect
    def test_rename_without_reloaddir_returns_404_but_succeeds(self, shared_user_client, repo, uploaded_file):
        """reloaddir 是可选参数，缺省为 false。此时重命名**实际已经成功**，
        接口却返回 404，且响应体是 HTML 错误页而不是 JSON。

        影响：
          1. 操作成功却报失败，调用方会认为文件仍叫旧名字，与服务端认知不一致；
          2. 响应体是 HTML，客户端 r.json() 会直接抛异常；
          3. 调用方若据此重试，第二次会拿到 520（此时文件确实已不存在）。

        规避方式：调用时显式传 reloaddir=true。

        本用例锁定当前实际行为；服务端修复后此用例会失败，用于提醒复核缺陷单。
        """
        file_api = FileApi(shared_user_client)
        new_name = "renamed_without_reloaddir.txt"

        r = file_api.rename_file(repo["id"], uploaded_file, new_name)   # 不传 reloaddir
        assert r.status_code == 404, "服务端行为已变化，请复核缺陷单"
        assert "text/html" in r.headers.get("Content-Type", ""), "响应体类型已变化"

        # 关键：接口报 404，但文件其实已经改名成功
        assert file_api.get_file_info(repo["id"], f"/{new_name}").status_code == 200, "新文件名查不到"
        assert file_api.get_file_info(repo["id"], uploaded_file).status_code == 404, "旧文件名仍然存在"

    # ------------------------------------------------------------ 删除
    @allure.story("删除文件")
    @allure.title("删除文件成功且确实查不到了")
    def test_delete_file_success(self, shared_user_client, repo, uploaded_file):
        file_api = FileApi(shared_user_client)
        r = file_api.delete_file(repo["id"], uploaded_file)
        assert r.status_code == 200
        assert file_api.get_file_info(repo["id"], uploaded_file).status_code == 404

    @allure.story("删除文件")
    @allure.title("重复删除同一文件仍返回 200（清理动作不可信，已记录）")
    @pytest.mark.defect
    def test_delete_file_is_idempotent_with_200(self, shared_user_client, repo, uploaded_file):
        """删除不存在的文件同样返回 200 "success"。

        这条行为直接决定了清理逻辑怎么写：不能靠 delete 的状态码判断"脏数据清干净了"，
        否则文件没删掉也不会报错，脏数据会一直累积。
        """
        file_api = FileApi(shared_user_client)
        assert file_api.delete_file(repo["id"], uploaded_file).status_code == 200
        r = file_api.delete_file(repo["id"], uploaded_file)
        assert r.status_code == 200, "服务端行为已变化，请复核"
        assert r.json() == "success"
