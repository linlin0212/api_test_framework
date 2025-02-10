import logging
import logging.config
import yaml
import os
from datetime import datetime

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'logger'):
            # 创建logs目录
            if not os.path.exists('logs'):
                os.makedirs('logs')

            # 读取日志配置
            with open('config/logging_config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 更新日志文件名，添加时间戳
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            config['handlers']['file']['filename'] = f'logs/test_{timestamp}.log'
            
            # 配置日志
            logging.config.dictConfig(config)
            self.logger = logging.getLogger('api_test')

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message) 