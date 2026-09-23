"""测试数据生成。"""
import time
import uuid


def _unique_suffix() -> str:
    # 加时间戳是为了事后能在服务端按名称排查残留数据
    return f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def unique_email(prefix: str = "autotest") -> str:
    return f"{prefix}_{_unique_suffix()}@qq.com"


def unique_repo_name(prefix: str = "autotest_repo") -> str:
    return f"{prefix}_{_unique_suffix()}"
