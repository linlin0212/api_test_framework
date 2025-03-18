import pytest
import allure
import json
import time
from datetime import datetime
from common.http_client import HTTPClient
from common.assertions import Assertions
from common.yaml_handler import YamlHandler
from common.variable_handler import VariableHandler

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
class TestAPI:
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
    
    @allure.feature("API测试用例")
    @pytest.mark.parametrize("case", YamlHandler.read_yaml("data/test_data.yaml")["test_cases"])
    def test_api(self, case):
        """API测试用例"""
        allure.dynamic.title(case["case_name"])
        allure.dynamic.description(f"测试接口: {case['path']}")
        
        # 如果是需要token的接口，检查token是否需要刷新
        if "headers" in case and "Authorization" in case["headers"]:
            if not self.token_manager.is_token_valid():
                self.refresh_token()
        
        # 替换请求数据中的变量
        if "headers" in case:
            case["headers"] = self.variable_handler.replace_variables(case["headers"])
        if "data" in case:
            case["data"] = self.variable_handler.replace_variables(case["data"])
        
        with allure.step(f"准备请求数据"):
            headers = case.get("headers", {})
            if "Authorization" in headers:
                headers["Authorization"] = headers["Authorization"].format(
                    token=self.token_manager.get_token()
                )
            allure.attach(
                json.dumps(case.get("data", {}), ensure_ascii=False, indent=2),
                "请求数据",
                allure.attachment_type.JSON
            )
        
        # 发送请求
        with allure.step(f"发送{case['method']}请求到 {case['path']}"):
            request_kwargs = {
                'method': case["method"],
                'path': case["path"],
                'service': case.get("service"),
                'headers': case.get("headers")
            }
            
            # 添加请求数据
            if case.get("data"):
                if case["method"].upper() == "GET":
                    request_kwargs['data'] = case["data"]
                else:
                    request_kwargs['json'] = case["data"]
            
            response = self.http_client.request(**request_kwargs)
            allure.attach(
                json.dumps(response.json(), ensure_ascii=False, indent=2),
                "响应数据",
                allure.attachment_type.JSON
            )
        
        # 保存需要的变量
        if "save_variables" in case and response.status_code == 200:
            with allure.step("保存接口返回变量"):
                self.variable_handler.save_variables(
                    response.json(),
                    case["save_variables"]
                )
        
        # 断言处理
        expected = case["expected"]
        with allure.step("执行断言"):
            # 状态码断言
            if "status_code" in expected:
                self.assertions.assert_status_code(response, expected["status_code"])
            
            # 字段类型断言
            if "field_types" in expected:
                for jsonpath_expr, expected_type in expected["field_types"].items():
                    with allure.step(f"验证字段类型: {jsonpath_expr}"):
                        # 传入的类型可能是字符串，需要转换为实际类型
                        if isinstance(expected_type, str):
                            expected_type = eval(expected_type)
                        self.assertions.assert_field_type(response, jsonpath_expr, expected_type)
            
            # 字段值断言
            if "field_values" in expected:
                for jsonpath_expr, value in expected["field_values"].items():
                    with allure.step(f"验证字段值: {jsonpath_expr}"):
                        self.assertions.assert_field_value(response, jsonpath_expr, value)
            
            # 数组断言
            if "array_assertions" in expected:
                for jsonpath_expr, assertions in expected["array_assertions"].items():
                    with allure.step(f"验证数组: {jsonpath_expr}"):
                        if "length" in assertions:
                            self.assertions.assert_array_length(response, jsonpath_expr, assertions["length"])
                        if "contains" in assertions:
                            for item in assertions["contains"]:
                                self.assertions.assert_array_contains(response, jsonpath_expr, item)
                        if "match" in assertions:
                            match_field = assertions["match"]["field"]
                            match_value = assertions["match"]["value"]
                            self.assertions.assert_array_matches(
                                response, 
                                jsonpath_expr,
                                lambda x: x.get(match_field) == match_value
                            )
            
            # 整体响应断言
            if "response_body" in expected:
                with allure.step("验证完整响应结构"):
                    self.assertions.assert_response_body(response, expected["response_body"])
        
        # 如果是登录接口，保存token
        if case["path"] == "/api/login" and response.status_code == 200:
            with allure.step("保存登录token"):
                response_data = response.json()
                self.token_manager.set_token(
                    response_data.get("token"),
                    response_data.get("expire_time")
                )

                allure.attach("Token已保存", f"token: {self.token_manager.get_token()}", allure.attachment_type.TEXT)

