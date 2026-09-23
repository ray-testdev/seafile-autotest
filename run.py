"""一键执行入口：跑用例 + 生成 Allure 报告。

用法：
    python run.py              全量执行
    python run.py -k login     只跑名字含 login 的用例（其余参数透传给 pytest）

关于 Allure：
    pytest 执行时通过 --alluredir 产出的是**原始结果**（一堆 JSON），
    要生成可浏览的 HTML 报告还需要 allure 命令行工具（依赖 Java）。
    本机没装时脚本会给出提示并正常退出，不影响用例执行结果。
"""
import shutil
import subprocess
import sys

import pytest

ALLURE_RESULTS = "allure-results"
ALLURE_REPORT = "allure-report"

if __name__ == "__main__":
    args = sys.argv[1:] or ["-v", f"--alluredir={ALLURE_RESULTS}"]

    exit_code = pytest.main(args)

    if exit_code != 0:
        sys.exit(exit_code)

    if shutil.which("allure") is None:
        print(
            "\n[提示] 未检测到 allure 命令行工具，跳过 HTML 报告生成。\n"
            f"       原始结果已保存在 {ALLURE_RESULTS}/，安装后可执行：\n"
            f"       allure generate {ALLURE_RESULTS} -o {ALLURE_REPORT} --clean\n"
            "       安装方式：先装 JDK，再装 allure-commandline 并配置 PATH。"
        )
        sys.exit(0)

    # 用 subprocess 而不是 os.system：参数以列表传入，不经过 shell，路径带空格也不会出错，
    # 而且能拿到执行结果、失败也不会被静默忽略。
    subprocess.run(
        ["allure", "generate", ALLURE_RESULTS, "-o", ALLURE_REPORT, "--clean"],
        check=False,
    )
    print(f"\nAllure 报告已生成：{ALLURE_REPORT}/index.html")
