import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from common.yaml_handler import YamlHandler
from common.logger import Logger

class EmailHandler:
    def __init__(self):
        self.logger = Logger()
        self.config = YamlHandler.read_yaml("config/config.yaml")
        self.email_config = self.config['email']

    def send_report(self, html_report_path=None):
        """
        发送测试报告邮件
        :param html_report_path: HTML报告路径
        """
        try:
            # 记录邮件配置信息（密码除外）
            self.logger.info(f"邮件配置信息:")
            self.logger.info(f"SMTP服务器: {self.email_config['smtp_host']}")
            self.logger.info(f"SMTP端口: {self.email_config['smtp_port']}")
            self.logger.info(f"发件人: {self.email_config['sender']}")
            self.logger.info(f"收件人: {self.email_config['receivers']}")

            # 创建邮件对象
            message = MIMEMultipart()
            message['From'] = self.email_config['sender']
            message['To'] = ','.join(self.email_config['receivers'])
            message['Subject'] = self.email_config['subject']

            # 邮件正文
            content = self._generate_email_content()
            message.attach(MIMEText(content, 'html', 'utf-8'))

            # 添加HTML报告附件
            if html_report_path and os.path.exists(html_report_path):
                self.logger.info(f"添加附件: {html_report_path}")
                with open(html_report_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment.add_header('Content-Disposition', 'attachment', 
                                       filename=os.path.basename(html_report_path))
                    message.attach(attachment)
            else:
                self.logger.warning(f"报告文件不存在: {html_report_path}")

            # 连接SMTP服务器
            self.logger.info("正在连接SMTP服务器...")
            smtp = smtplib.SMTP_SSL(self.email_config['smtp_host'], 
                                  self.email_config['smtp_port'])
            smtp.set_debuglevel(1)  # 开启DEBUG模式
            
            # 登录
            self.logger.info("正在登录SMTP服务器...")
            smtp.login(self.email_config['sender'], 
                      self.email_config['password'])

            # 发送邮件
            self.logger.info("正在发送邮件...")
            smtp.send_message(message)
            
            # 关闭连接
            smtp.quit()

            self.logger.info("测试报告邮件发送成功")
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP认证失败: {str(e)}")
            self.logger.error("请检查邮箱账号和授权码是否正确")
            raise
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP错误: {str(e)}")
            self.logger.error("请检查SMTP服务器配置是否正确")
            raise
        except FileNotFoundError as e:
            self.logger.error(f"文件未找到: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"发送邮件时发生未知错误: {str(e)}")
            self.logger.error(f"错误类型: {type(e).__name__}")
            raise

    def _generate_email_content(self):
        """
        生成带有测试统计信息的邮件正文
        """
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #333;">API自动化测试报告</h2>
                <p>您好，</p>
                <p>本次自动化测试已完成，详细测试报告请查看附件。</p>
                <p style="color: #666;">注：本邮件由自动化测试系统发送，请勿回复。</p>
            </body>
        </html>
        """ 