import pytest
import allure
import platform
import os
from datetime import datetime

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    用于在测试报告中添加用例时间、错误截图等
    """
    outcome = yield
    report = outcome.get_result()
    
    # 添加用例开始时间
    if report.when == "call":
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        allure.dynamic.description(f'\n测试开始时间：{start_time}')
        
        # 如果用例失败，则添加失败信息
        if report.failed:
            if hasattr(report, "wasxfail"):
                # 预期失败的用例
                allure.dynamic.description(f'预期失败: {report.wasxfail}')
            else:
                # 意外失败的用例
                allure.dynamic.description(f'失败原因: {report.longrepr}')

@pytest.fixture(scope="session", autouse=True)
def configure_allure_environment():
    """配置Allure环境信息"""
    # 确保reports目录存在
    if not os.path.exists("reports/allure_results"):
        os.makedirs("reports/allure_results")
    
    # 创建environment.properties文件
    env_file = "reports/allure_results/environment.properties"
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(f"Python.Version={platform.python_version()}\n")
        f.write(f"Platform={platform.system()}\n")
        f.write(f"Host=localhost\n")
        f.write(f"Testing.Environment=test\n")