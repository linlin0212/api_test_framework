import os
import subprocess
import time
from datetime import datetime

def run_tests():
    """运行测试并生成Allure报告"""
    # 创建报告目录
    if not os.path.exists("reports"):
        os.makedirs("reports")
    
    # 运行测试
    print("开始执行测试...")
    pytest_cmd = "pytest"
    subprocess.run(pytest_cmd, shell=True)
    
    # 生成Allure报告
    print("正在生成Allure报告...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/html_{timestamp}"
    
    # 生成HTML报告
    allure_cmd = f"allure generate reports/allure_results -o {report_path} --clean"
    subprocess.run(allure_cmd, shell=True)
    
    # 打开报告
    print(f"正在打开测试报告...")
    open_cmd = f"allure open {report_path}"
    subprocess.run(open_cmd, shell=True)

if __name__ == "__main__":
    run_tests() 