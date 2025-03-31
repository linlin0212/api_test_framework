import json
import allure
from common.http_client import HTTPClient
from common.assertions import Assertions
from common.yaml_handler import YamlHandler
from common.variable_handler import VariableHandler

class TestBase:
    def setup_class(self):
        self.http_client = HTTPClient()
        self.assertions = Assertions()
        self.test_data = YamlHandler.read_yaml("data/test_data.yaml")
        self.variable_handler = VariableHandler()

    def execute_test_step(self, step, step_name=None):
        """
        执行测试步骤
        :param step: 步骤配置
        :param step_name: 步骤名称（可选）
        """
        with allure.step(step_name or f"执行接口: {step['path']}"):
            # 替换变量
            self._prepare_request_data(step)
            
            # 发送请求
            response = self._send_request(step)
            
            # 保存变量
            self._save_response_variables(step, response)
            
            # 执行断言
            self._perform_assertions(step, response)
            
            return response

    def _prepare_request_data(self, step):
        """准备请求数据，替换变量"""
        # 替换请求数据中的变量
        if "headers" in step:
            step["headers"] = self.variable_handler.replace_variables(step["headers"])
        if "data" in step:
            step["data"] = self.variable_handler.replace_variables(step["data"])
        # 替换URL中的变量
        step["path"] = self.variable_handler.replace_variables(step["path"])

        # 记录请求数据
        with allure.step(f"准备请求数据"):
            allure.attach(
                json.dumps(step.get("data", {}), ensure_ascii=False, indent=2),
                "请求数据",
                allure.attachment_type.JSON
            )

    def _send_request(self, step):
        """发送HTTP请求"""
        with allure.step(f"发送{step['method']}请求到 {step['path']}"):
            request_kwargs = {
                'method': step["method"],
                'path': step["path"],
                'service': step.get("service"),
                'headers': step.get("headers")
            }
            
            # 添加请求数据
            if step.get("data"):
                if step["method"].upper() == "GET":
                    request_kwargs['data'] = step["data"]
                else:
                    request_kwargs['json'] = step["data"]
            
            response = self.http_client.request(**request_kwargs)
            allure.attach(
                json.dumps(response.json(), ensure_ascii=False, indent=2),
                "响应数据",
                allure.attachment_type.JSON
            )
            return response

    def _save_response_variables(self, step, response):
        """保存响应中的变量"""
        if "save_variables" in step and response.status_code == 200:
            with allure.step("保存接口返回变量"):
                self.variable_handler.save_variables(
                    response.json(),
                    step["save_variables"]
                )

    def _perform_assertions(self, step, response):
        """执行断言"""
        expected = step["expected"]
        with allure.step("执行断言"):
            # 状态码断言
            if "status_code" in expected:
                self.assertions.assert_status_code(response, expected["status_code"])
            
            # 字段存在性断言
            if "contains_fields" in expected:
                for field in expected["contains_fields"]:
                    self.assertions.assert_contains_field(response, field)
            
            # 字段类型断言
            if "field_types" in expected:
                for jsonpath_expr, expected_type in expected["field_types"].items():
                    with allure.step(f"验证字段类型: {jsonpath_expr}"):
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