import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from common.logger import Logger
from common.email_handler import EmailHandler

class TestRunner:
    def __init__(self):
        self.logger = Logger()
        self.email_handler = EmailHandler()

    def check_allure_installation(self):
        """检查 Allure 是否已安装"""
        try:
            # Windows系统下需要检查 allure.bat
            if sys.platform.startswith('win'):
                # 检查环境变量中的 allure
                allure_cmd = "where allure"
            else:
                allure_cmd = "which allure"
            
            result = subprocess.run(allure_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"找到 Allure 安装路径: {result.stdout.strip()}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"检查 Allure 安装时出错: {str(e)}")
            return False

    def open_report(self, report_path):
        """
        打开测试报告
        :param report_path: 报告路径
        """
        try:
            # 检查报告目录是否存在
            if not os.path.exists(report_path):
                self.logger.error(f"报告目录不存在: {report_path}")
                return False

            self.logger.info("正在使用 allure 命令打开报告...")
            try:
                # 优先尝试使用 allure open
                if sys.platform.startswith('win'):
                    subprocess.Popen(["allure", "open", report_path], shell=True)
                else:
                    # 在类Unix系统上使用 allure serve
                    subprocess.Popen(["allure", "serve", report_path], shell=True)
                return True
            except Exception as e:
                self.logger.warning(f"使用 allure 命令打开报告失败: {str(e)}")
                self.logger.info("尝试使用默认浏览器打开...")
                
                # 如果 allure 命令失败，尝试使用浏览器打开
                index_path = os.path.join(report_path, "index.html")
                if os.path.exists(index_path):
                    webbrowser.open(f"file://{os.path.abspath(index_path)}")
                    return True
                else:
                    self.logger.error(f"报告文件不存在: {index_path}")
                    return False
                
        except Exception as e:
            self.logger.error(f"打开报告失败: {str(e)}")
            return False

    def run_tests(self):
        """运行测试并生成Allure报告"""
        try:
            # 检查 Allure 是否安装
            if not self.check_allure_installation():
                self.logger.error("Allure 未安装或未添加到环境变量，请先安装 Allure")
                self.logger.info("安装说明：")
                self.logger.info("1. 下载 Allure: https://github.com/allure-framework/allure2/releases")
                self.logger.info("2. 解压到指定目录")
                self.logger.info("3. 将bin目录添加到环境变量")
                return False

            # 创建报告目录
            if not os.path.exists("reports"):
                os.makedirs("reports")
            
            # 运行测试
            self.logger.info("开始执行测试...")
            pytest_result = subprocess.run(
                ["pytest"], 
                capture_output=True, 
                text=True
            )
            
            # 输出测试结果
            print(pytest_result.stdout)
            if pytest_result.stderr:
                print(pytest_result.stderr)

            # 生成Allure报告
            self.logger.info("正在生成Allure报告...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.abspath(f"reports/html_{timestamp}")

            try:
                # 生成HTML报告
                self.logger.info(f"正在生成报告到: {report_path}")
                subprocess.run([
                    "allure", 
                    "generate", 
                    "reports/allure_results",
                    "-o", 
                    report_path,
                    "--clean"
                ], shell=True, check=True)

                # 发送邮件
                self.logger.info("正在发送测试报告邮件...")
                self.email_handler.send_report(f"{report_path}/index.html")
                
                # 打开报告
                self.logger.info("正在尝试打开测试报告...")
                self.open_report(report_path)

            except subprocess.CalledProcessError as e:
                self.logger.error(f"生成报告失败: {str(e)}")
                raise
            except Exception as e:
                self.logger.error(f"处理报告过程中出错: {str(e)}")
                raise

            self.logger.info(f"测试执行完成，报告路径：{report_path}")
            
            # 返回测试是否全部通过
            return pytest_result.returncode == 0

        except subprocess.CalledProcessError as e:
            self.logger.error(f"命令执行失败: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"运行测试过程中出错: {str(e)}")
            raise

if __name__ == "__main__":
    runner = TestRunner()
    try:
        success = runner.run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 