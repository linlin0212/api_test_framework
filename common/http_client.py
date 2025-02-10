import requests
import json
from common.logger import Logger
from common.yaml_handler import YamlHandler

class HTTPClient:
    def __init__(self):
        self.logger = Logger()
        self.config = YamlHandler.read_yaml("config/config.yaml")
        self.session = requests.Session()
        self.env = self.config['environment']
        self.base_url = self.config['env'][self.env]['base_url']
        
        # 设置基本请求头
        self.session.headers.update(self.config['headers'])
        
        # 设置SSL验证和超时
        self.session.verify = self.config['env'][self.env]['verify_ssl']
        self.timeout = self.config['env'][self.env]['timeout']

    def request(self, method, path, **kwargs):
        """
        发送HTTP请求
        :param method: 请求方法
        :param path: 接口路径
        :param kwargs: 请求参数
        :return: 响应对象
        """
        url = self.base_url + path
        method = method.upper()
        
        # 记录请求信息
        self.logger.info(f"Request URL: {url}")
        self.logger.info(f"Request Method: {method}")
        self.logger.info(f"Request Headers: {self.session.headers}")
        
        if 'json' in kwargs:
            self.logger.info(f"Request Body: {json.dumps(kwargs['json'], ensure_ascii=False)}")
        elif 'data' in kwargs:
            self.logger.info(f"Request Data: {kwargs['data']}")
        
        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        try:
            response = self.session.request(method, url, **kwargs)
            
            # 记录响应信息
            self.logger.info(f"Response Status Code: {response.status_code}")
            self.logger.info(f"Response Headers: {response.headers}")
            try:
                self.logger.info(f"Response Body: {json.dumps(response.json(), ensure_ascii=False)}")
            except:
                self.logger.info(f"Response Text: {response.text}")
                
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Request Failed: {str(e)}")
            raise 