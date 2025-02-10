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
                with open(html_report_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment.add_header('Content-Disposition', 'attachment', 
                                       filename=os.path.basename(html_report_path))
                    message.attach(attachment)

            # 发送邮件
            with smtplib.SMTP_SSL(self.email_config['smtp_host'], 
                                self.email_config['smtp_port']) as smtp:
                smtp.login(self.email_config['sender'], 
                         self.email_config['password'])
                smtp.send_message(message)

            self.logger.info("测试报告邮件发送成功")
            
        except Exception as e:
            self.logger.error(f"发送邮件失败: {str(e)}")
            raise

    def _generate_email_content(self):
        """
        生成带有测试统计信息的邮件正文
        """
        # 读取测试结果统计（需要实现获取测试结果的逻辑）
        total = 100
        passed = 80
        failed = 15
        skipped = 5
        
        return f"""
        <html>
            <body>
                <h2>API自动化测试报告</h2>
                <p>测试统计信息：</p>
                <ul>
                    <li>总用例数：{total}</li>
                    <li>通过：{passed}</li>
                    <li>失败：{failed}</li>
                    <li>跳过：{skipped}</li>
                </ul>
                <p>通过率：{passed/total*100:.2f}%</p>
                <p>详细信息请查看附件中的测试报告。</p>
                <p>本邮件由自动化测试系统发送，请勿回复。</p>
            </body>
        </html>
        """ 