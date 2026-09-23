"""文件接口。"""
from api.client import BaseApi


class FileApi(BaseApi):

    def get_upload_link(self, repo_id):
        """GET /api2/repos/{repo_id}/upload-link/

        响应体是 JSON 字符串（形如 "http://host/seafhttp/upload-api/xxx"），
        必须用 .json() 取；用 .text 会带上首尾引号，拿去做 URL 会直接抛异常。
        """
        return self.client.request("GET", f"api2/repos/{repo_id}/upload-link/")

    def upload_file(self, upload_link, file_path, parent_dir="/", relative_path=None, ret_json=None):
        """POST 上传链接（multipart 表单）。"""
        params = {}
        if relative_path is not None:
            params["relative_path"] = relative_path
        if ret_json is not None:
            params["ret-json"] = ret_json

        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"parent_dir": parent_dir}
            return self.client.request("POST", upload_link, files=files, data=data, params=params)

    def get_download_link(self, repo_id, p, reuse=None):
        """GET /api2/repos/{repo_id}/file/?p=/x.txt

        路径为空/缺失 400；文件不存在 404；成功返回下载 URL 字符串。
        """
        params = {"p": p}
        if reuse is not None:
            params["reuse"] = reuse
        return self.client.request("GET", f"api2/repos/{repo_id}/file/", params=params)

    def download_file(self, download_link):
        """下载链接是完整 URL，直接请求即可拿到文件内容。"""
        return self.client.request("GET", download_link)

    def get_file_info(self, repo_id, p):
        """GET /api2/repos/{repo_id}/file/detail/?p=/x.txt"""
        return self.client.request("GET", f"api2/repos/{repo_id}/file/detail/", params={"p": p})

    def rename_file(self, repo_id, p, newname, operation="rename", reloaddir=None):
        """POST /api2/repos/{repo_id}/file/?p=/x.txt

        新名字与旧名字相同 409；目标文件不存在会返回 520（非标准状态码，见缺陷报告）。
        """
        data = {"newname": newname, "operation": operation}
        params = {"p": p}
        if reloaddir is not None:
            params["reloaddir"] = reloaddir
        return self.client.request("POST", f"api2/repos/{repo_id}/file/", data=data, params=params)

    def delete_file(self, repo_id, p):
        """DELETE /api2/repos/{repo_id}/file/?p=/x.txt

        删除不存在的文件同样返回 200 "success"，不能靠这个状态码确认清理是否生效。
        """
        return self.client.request("DELETE", f"api2/repos/{repo_id}/file/", params={"p": p})
