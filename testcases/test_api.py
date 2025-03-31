import pytest
import allure
import json
import time
from datetime import datetime
from common.http_client import HTTPClient
from common.assertions import Assertions
from common.yaml_handler import YamlHandler
from common.variable_handler import VariableHandler
from testcases.test_base import TestBase

class TokenManager:
    def __init__(self):
        self.token = None
        self.expire_time = None
        self.yaml_handler = YamlHandler()
        self.token_config = self.yaml_handler.read_yaml("data/test_data.yaml")["token_config"]

    def set_token(self, token, expire_time=None):
        """
        设置token和过期时间
        :param token: token字符串
        :param expire_time: 过期时间戳（秒）
        """
        self.token = token
        if expire_time:
            self.expire_time = expire_time
        else:
            # 如果没有提供过期时间，使用配置的默认过期时间
            self.expire_time = time.time() + self.token_config["expire_time"]

    def is_token_valid(self):
        """
        检查token是否有效
        :return: bool
        """
        if not self.token or not self.expire_time:
            return False
        
        # 检查是否接近过期时间
        remaining_time = self.expire_time - time.time()
        return remaining_time > self.token_config["refresh_before_expire"]

    def get_token(self):
        """
        获取token
        :return: token字符串
        """
        return self.token

@allure.epic("API自动化测试")
@allure.feature("单接口测试")
class TestAPI(TestBase):
    def setup_class(self):
        self.http_client = HTTPClient()
        self.assertions = Assertions()
        self.test_data = YamlHandler.read_yaml("data/test_data.yaml")
        self.token_manager = TokenManager()
        self.variable_handler = VariableHandler()
    
    def refresh_token(self):
        """
        刷新token
        """
        with allure.step("刷新token"):
            # 获取登录测试用例数据
            login_case = next(
                case for case in self.test_data["test_cases"] 
                if case["path"] == "/api/login"
            )
            
            # 发送登录请求
            response = self.http_client.request(
                method=login_case["method"],
                path=login_case["path"],
                json=login_case["data"]
            )
            
            # 验证登录响应
            assert response.status_code == 200, "登录失败，无法刷新token"
            
            # 获取新token和过期时间
            response_data = response.json()
            new_token = response_data.get("token")
            expire_time = response_data.get("expire_time")  # 假设接口返回过期时间戳
            
            # 更新token管理器
            self.token_manager.set_token(new_token, expire_time)
            allure.attach("Token已刷新", f"新token: {new_token}", allure.attachment_type.TEXT)
    
    @allure.story("接口用例")
    @pytest.mark.parametrize("case", YamlHandler.read_yaml("data/test_data.yaml")["test_cases"])
    def test_api(self, case):
        """单接口测试用例"""
        allure.dynamic.title(case["case_name"])
        
        # 执行测试步骤
        self.execute_test_step(case)

