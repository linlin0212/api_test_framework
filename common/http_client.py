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
        
        # 设置基本请求头
        self.session.headers.update(self.config['headers'])

    def get_service_config(self, service_name=None):
        """
        获取服务配置
        :param service_name: 服务名称，如果为None则使用默认配置
        :return: 服务配置字典
        """
        if not service_name:
            service_name = 'default'
            
        try:
            return self.config['env'][self.env][service_name]
        except KeyError:
            self.logger.warning(f"未找到服务 {service_name} 的配置，使用默认配置")
            return self.config['env'][self.env]['default']

    def request(self, method, path, service=None, **kwargs):
        """
        发送HTTP请求
        :param method: 请求方法
        :param path: 接口路径
        :param service: 服务名称
        :param kwargs: 请求参数
        :return: 响应对象
        """
        # 获取服务配置
        service_config = self.get_service_config(service)
        base_url = service_config['base_url']
        url = base_url + path
        method = method.upper()
        
        # 记录请求信息
        self.logger.info(f"Service: {service or 'default'}")
        self.logger.info(f"Environment: {self.env}")
        self.logger.info(f"Request URL: {url}")
        self.logger.info(f"Request Method: {method}")
        self.logger.info(f"Request Headers: {self.session.headers}")
        
        if 'json' in kwargs:
            self.logger.info(f"Request Body: {json.dumps(kwargs['json'], ensure_ascii=False)}")
        elif 'data' in kwargs:
            self.logger.info(f"Request Data: {kwargs['data']}")
        
        # 设置超时和SSL验证
        kwargs.setdefault('timeout', service_config.get('timeout', 30))
        kwargs.setdefault('verify', service_config.get('verify_ssl', True))

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