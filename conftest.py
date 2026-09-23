"""全局 Fixture：登录身份与测试数据的创建、销毁。

作用域划分：
  session  —— 登录身份和共享测试账号，整个会话只建一次；
  function —— 所有会产生数据的对象（临时账号、资料库、已上传文件），
              每条用例一份，用完即删。

数据清理写在 yield 之后，pytest 保证用例失败时它也会执行；
写成 return 就变成"只建不删"，跑几十条用例后服务端会堆满无主资料库。
"""
import socket
from urllib.parse import urlparse

import pytest

from api.account_api import AccountApi
from api.auth_api import AuthApi
from api.client import SeafileClient
from api.file_api import FileApi
from api.repo_api import RepoApi
from common.config import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    BASE_URL,
    MEMBER_EMAIL,
    MEMBER_PASSWORD,
    REMOTE_FILE_PATH,
    REPO_PASSWORD,
    TEST_PASSWORD,
    UPLOAD_FILE,
)
from common.utils import unique_email, unique_repo_name


def _login(client, email, password, role):
    resp = AuthApi(client).login(email, password)
    if resp.status_code == 429:
        pytest.fail(
            f"{role} 账号登录被限流（429）：{resp.text[:120]}\n"
            f"Seafile 对 /api2/auth-token/ 有频率限制，等约 1 分钟再执行。"
        )
    if resp.status_code != 200:
        pytest.fail(
            f"{role} 账号 {email} 登录失败，返回 {resp.status_code}。"
            f"请确认 {BASE_URL} 可访问、账号密码正确。响应：{resp.text[:200]}"
        )
    return client


def _server_reachable() -> bool:
    """只做一次 TCP 连接探测，不发业务请求。"""
    parsed = urlparse(BASE_URL)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except OSError:
        return False


def pytest_collection_modifyitems(config, items):
    """被测服务不可达时整体跳过，并说明原因。

    这套用例依赖一个真实部署的 Seafile 实例。换台机器、或者服务没起来的时候，
    让几十条用例各自报一次连接超时毫无意义，报错也指不到重点。
    """
    if _server_reachable():
        return
    reason = (
        f"被测服务 {BASE_URL} 不可达，跳过全部接口用例。"
        f"本套件需要一个可达的 Seafile 实例，"
        f"请先部署并把地址写入环境变量 SEAFILE_BASE_URL（见 README 快速开始一节）。"
    )
    for item in items:
        item.add_marker(pytest.mark.skip(reason=reason))


# ------------------------------------------------------------------ 登录身份
@pytest.fixture(scope="session")
def admin_client():
    client = _login(SeafileClient(BASE_URL), ADMIN_EMAIL, ADMIN_PASSWORD, "管理员")
    yield client
    client.close()


@pytest.fixture(scope="session")
def member_client():
    """普通成员，用来验证越权访问会被拒绝。"""
    client = _login(SeafileClient(BASE_URL), MEMBER_EMAIL, MEMBER_PASSWORD, "普通成员")
    yield client
    client.close()


@pytest.fixture(scope="session")
def shared_user(admin_client):
    """资料库/文件模块共用的测试账号。

    不按用例建账号是为了控制登录次数：这个接口有频率限制，
    每条用例都登录会直接把限流打满，第二次执行就大面积失败。
    用例之间的隔离由"每条用例一个独立资料库"保证，账号只是容器。
    """
    email = unique_email("autotest_shared")
    AccountApi(admin_client).admin_create_account(email, TEST_PASSWORD)
    yield {"email": email, "password": TEST_PASSWORD}
    AccountApi(admin_client).admin_delete_account(email)


@pytest.fixture(scope="session")
def shared_user_client(shared_user):
    client = SeafileClient(BASE_URL)
    _login(client, shared_user["email"], shared_user["password"], "共享测试账号")
    yield client
    client.close()


# ------------------------------------------------------------------ 一次性身份
@pytest.fixture
def disposable_account(admin_client):
    """一次性账号，给测账号接口本身的用例用。"""
    email = unique_email()
    AccountApi(admin_client).admin_create_account(email, TEST_PASSWORD)
    yield {"email": email, "password": TEST_PASSWORD}
    AccountApi(admin_client).admin_delete_account(email)


@pytest.fixture
def disposable_client(disposable_account):
    client = SeafileClient(BASE_URL)
    AuthApi(client).login(disposable_account["email"], disposable_account["password"])
    yield client
    client.close()


@pytest.fixture
def bad_token_client(admin_client):
    """Token 非法的客户端。

    在真实 token 后面加一个字符，而不是随手写个字符串：这样走的是
    "格式合法但服务端不认识"那条分支。如果写成含空格的字符串，
    服务端会返回 "Token string should not contain spaces"，测到的就不是同一回事了。
    """
    client = SeafileClient(BASE_URL, token=f"{admin_client.token}1")
    yield client
    client.close()


@pytest.fixture
def anonymous_client():
    """不带 Token，用于验证未认证时的返回码。"""
    client = SeafileClient(BASE_URL)
    yield client
    client.close()


# ------------------------------------------------------------------ 业务数据
@pytest.fixture
def repo(shared_user_client):
    """临时资料库，用例结束后整库删除。

    返回 dict 而不是裸 repo_id，是因为后面经常要拿库名做断言。
    """
    repo_api = RepoApi(shared_user_client)
    name = unique_repo_name()
    resp = repo_api.create_repo(name)
    assert resp.status_code == 200, f"前置资料库创建失败：{resp.status_code} {resp.text[:200]}"
    repo_id = resp.json()["repo_id"]
    yield {"id": repo_id, "name": name}
    repo_api.delete_repo(repo_id)


@pytest.fixture
def encrypted_repo(shared_user_client):
    repo_api = RepoApi(shared_user_client)
    name = unique_repo_name("autotest_enc")
    resp = repo_api.create_encrypted_repo(name, REPO_PASSWORD)
    assert resp.status_code == 200, f"前置加密资料库创建失败：{resp.status_code} {resp.text[:200]}"
    repo_id = resp.json()["repo_id"]
    yield {"id": repo_id, "name": name, "password": REPO_PASSWORD}
    repo_api.delete_repo(repo_id)


@pytest.fixture
def uploaded_file(shared_user_client, repo):
    """资料库中预先上传一个文件，返回它的服务端路径。"""
    file_api = FileApi(shared_user_client)
    upload_link = file_api.get_upload_link(repo["id"]).json()
    resp = file_api.upload_file(upload_link, UPLOAD_FILE)
    assert resp.status_code == 200, f"前置文件上传失败：{resp.status_code} {resp.text[:200]}"
    # 不需要单独删文件：repo fixture 会把整个资料库删掉。
    # 而且实测 delete_file 对不存在的文件也返回 200，靠它确认清理结果并不可靠。
    return REMOTE_FILE_PATH
