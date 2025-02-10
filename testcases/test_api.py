import pytest
import allure
import json
from common.http_client import HTTPClient
from common.assertions import Assertions
from common.yaml_handler import YamlHandler

@allure.epic("API自动化测试")
class TestAPI:
    def setup_class(self):
        self.http_client = HTTPClient()
        self.assertions = Assertions()
        self.test_data = YamlHandler.read_yaml("data/test_data.yaml")
        self.token = None  # 用于存储登录token
    
    @allure.feature("API测试用例")
    @pytest.mark.parametrize("case", YamlHandler.read_yaml("data/test_data.yaml")["test_cases"])
    def test_api(self, case):
        """API测试用例"""
        # 添加测试标题
        allure.dynamic.title(case["case_name"])
        # 添加测试描述
        allure.dynamic.description(f"测试接口: {case['path']}")
        
        # 添加测试步骤
        with allure.step(f"准备请求数据"):
            headers = case.get("headers", {})
            if self.token and "Authorization" in headers:
                headers["Authorization"] = headers["Authorization"].format(token=self.token)
            allure.attach(
                json.dumps(case.get("data", {}), ensure_ascii=False, indent=2),
                "请求数据",
                allure.attachment_type.JSON
            )
        
        # 发送请求
        with allure.step(f"发送{case['method']}请求到 {case['path']}"):
            response = self.http_client.request(
                method=case["method"],
                path=case["path"],
                headers=headers,
                json=case.get("data")
            )
            # 添加响应结果
            allure.attach(
                json.dumps(response.json(), ensure_ascii=False, indent=2),
                "响应数据",
                allure.attachment_type.JSON
            )
        
        # 断言处理
        expected = case["expected"]
        with allure.step("执行断言"):
            # 状态码断言
            if "status_code" in expected:
                with allure.step(f"验证状态码: 期望 {expected['status_code']}"):
                    self.assertions.assert_status_code(response, expected["status_code"])
            
            # 字段存在性断言
            if "contains_fields" in expected:
                for field in expected["contains_fields"]:
                    with allure.step(f"验证字段存在: {field}"):
                        self.assertions.assert_contains_field(response, field)
            
            # 字段值断言
            if "field_values" in expected:
                for field, value in expected["field_values"].items():
                    with allure.step(f"验证字段值: {field} = {value}"):
                        self.assertions.assert_field_value(response, field, value)
        
        # 保存token
        if case["path"] == "/api/login" and response.status_code == 200:
            with allure.step("保存登录token"):
                self.token = response.json().get("token") 