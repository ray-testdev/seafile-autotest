"""全局配置。

地址、账号、密码一律从环境变量取，其次读项目根目录的 .env。
.env 已在 .gitignore 中，仓库里只留 .env.example 作为模板。
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        # 用 setdefault：CI 注入的环境变量优先于本地 .env
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(PROJECT_ROOT / ".env")


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"缺少环境变量 {name}。\n"
            f"  本地运行：复制 .env.example 为 .env 并填写实际值；\n"
            f"  CI 运行：在仓库 Settings -> Secrets 中配置同名 Secret。"
        )
    return value


def _optional(name: str, default: str) -> str:
    return os.getenv(name) or default


BASE_URL = _required("SEAFILE_BASE_URL").rstrip("/") + "/"
REQUEST_TIMEOUT = float(_optional("SEAFILE_TIMEOUT", "10"))

ADMIN_EMAIL = _required("SEAFILE_ADMIN_EMAIL")
ADMIN_PASSWORD = _required("SEAFILE_ADMIN_PASSWORD")

MEMBER_EMAIL = _required("SEAFILE_MEMBER_EMAIL")
MEMBER_PASSWORD = _required("SEAFILE_MEMBER_PASSWORD")

# 下面两个是给临时对象用的密码，不是真实凭据，因此给了默认值
TEST_PASSWORD = _optional("SEAFILE_TEST_PASSWORD", "user")
REPO_PASSWORD = _optional("SEAFILE_REPO_PASSWORD", "abC123456")

DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_FILE = DATA_DIR / "sample_upload.txt"
UPLOAD_FILE_NAME = UPLOAD_FILE.name
REMOTE_FILE_PATH = f"/{UPLOAD_FILE_NAME}"
