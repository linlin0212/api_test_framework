import json
import allure
from typing import Any, List, Dict
from jsonpath_ng import parse
from common.logger import Logger

class Assertions:
    def __init__(self):
        self.logger = Logger()

    def assert_status_code(self, response, expected_code):
        """断言响应状态码"""
        actual_code = response.status_code
        assert actual_code == expected_code, \
            f"断言状态码失败！预期: {expected_code}, 实际: {actual_code}"
        self.logger.info(f"状态码断言成功: {actual_code}")

    def assert_contains_field(self, response, jsonpath_expr):
        """
        断言响应包含指定字段 (使用JSONPath语法)
        :param response: 响应对象
        :param jsonpath_expr: JSONPath表达式，如 '$.data.items[0].id'
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            raise AssertionError("响应不是有效的JSON格式")

        jsonpath_expr = parse(jsonpath_expr)
        matches = [match.value for match in jsonpath_expr.find(response_data)]
        
        assert len(matches) > 0, f"JSONPath '{jsonpath_expr}' 未匹配到任何内容"
        self.logger.info(f"字段存在性断言成功: {jsonpath_expr}")

    def assert_field_value(self, response, jsonpath_expr, expected_value):
        """
        断言字段值 (使用JSONPath语法)
        :param response: 响应对象
        :param jsonpath_expr: JSONPath表达式，如 '$.data.items[0].name'
        :param expected_value: 期望值
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            raise AssertionError("响应不是有效的JSON格式")

        # 解析JSONPath表达式
        jsonpath_expr = parse(jsonpath_expr)
        matches = [match.value for match in jsonpath_expr.find(response_data)]
        
        assert len(matches) > 0, f"JSONPath '{jsonpath_expr}' 未匹配到任何内容"
        actual_value = matches[0]  # 取第一个匹配结果
        
        # 根据期望值类型进行不同的断言
        if isinstance(expected_value, (int, float, str, bool)):
            assert actual_value == expected_value, \
                f"字段值断言失败！JSONPath: {jsonpath_expr}, 预期: {expected_value}, 实际: {actual_value}"
        elif isinstance(expected_value, dict):
            self._assert_dict_value(actual_value, expected_value, str(jsonpath_expr))
        elif isinstance(expected_value, list):
            self._assert_list_value(actual_value, expected_value, str(jsonpath_expr))
        else:
            raise ValueError(f"不支持的断言值类型: {type(expected_value)}")
            
        self.logger.info(f"字段值断言成功: {jsonpath_expr}")

    def assert_field_type(self, response, jsonpath_expr, expected_type):
        """
        断言字段类型 (使用JSONPath语法)
        :param response: 响应对象
        :param jsonpath_expr: JSONPath表达式
        :param expected_type: 期望的类型
        """
        jsonpath_expr = parse(jsonpath_expr)
        matches = [match.value for match in jsonpath_expr.find(response.json())]
        
        assert len(matches) > 0, f"JSONPath '{jsonpath_expr}' 未匹配到任何内容"
        actual_value = matches[0]  # 取第一个匹配结果
        
        assert isinstance(actual_value, expected_type), \
            f"字段类型断言失败！JSONPath: {jsonpath_expr}, 预期类型: {expected_type.__name__}, 实际类型: {type(actual_value).__name__}"
        self.logger.info(f"字段类型断言成功: {jsonpath_expr} 类型为 {expected_type.__name__}")

    def assert_array_length(self, response, jsonpath_expr, expected_length):
        """
        断言数组长度 (使用JSONPath语法)
        :param response: 响应对象
        :param jsonpath_expr: JSONPath表达式，指向数组
        :param expected_length: 期望长度
        """
        jsonpath_expr = parse(jsonpath_expr)
        matches = [match.value for match in jsonpath_expr.find(response.json())]
        
        assert len(matches) > 0, f"JSONPath '{jsonpath_expr}' 未匹配到任何内容"
        array_value = matches[0]  # 取第一个匹配结果
        
        assert isinstance(array_value, list), f"字段 {jsonpath_expr} 不是数组类型"
        actual_length = len(array_value)
        assert actual_length == expected_length, \
            f"数组长度断言失败！JSONPath: {jsonpath_expr}, 预期长度: {expected_length}, 实际长度: {actual_length}"
        self.logger.info(f"数组长度断言成功: {jsonpath_expr} 长度为 {actual_length}")

    def assert_array_contains(self, response, jsonpath_expr, expected_item):
        """
        断言数组包含特定元素 (使用JSONPath语法)
        :param response: 响应对象
        :param jsonpath_expr: JSONPath表达式，指向数组
        :param expected_item: 期望包含的元素
        """
        jsonpath_expr = parse(jsonpath_expr)
        matches = [match.value for match in jsonpath_expr.find(response.json())]
        
        assert len(matches) > 0, f"JSONPath '{jsonpath_expr}' 未匹配到任何内容"
        array_value = matches[0]  # 取第一个匹配结果
        
        assert isinstance(array_value, list), f"字段 {jsonpath_expr} 不是数组类型"
        
        # 检查数组中是否有匹配的项
        if isinstance(expected_item, dict):
            # 如果期望项是字典，进行部分匹配
            found = False
            for item in array_value:
                if isinstance(item, dict) and all(item.get(k) == v for k, v in expected_item.items()):
                    found = True
                    break
            assert found, f"数组中未找到包含所有期望键值对的项: {expected_item}"
        else:
            # 直接检查是否包含
            assert expected_item in array_value, \
                f"数组不包含期望元素！JSONPath: {jsonpath_expr}, 期望元素: {expected_item}"
                
        self.logger.info(f"数组包含元素断言成功: {jsonpath_expr} 包含 {expected_item}")

    def assert_array_matches(self, response, jsonpath_expr, match_func):
        """
        断言数组元素满足特定条件 (使用JSONPath语法)
        :param response: 响应对象
        :param jsonpath_expr: JSONPath表达式，指向数组
        :param match_func: 匹配函数，返回布尔值
        """
        jsonpath_expr = parse(jsonpath_expr)
        matches = [match.value for match in jsonpath_expr.find(response.json())]
        
        assert len(matches) > 0, f"JSONPath '{jsonpath_expr}' 未匹配到任何内容"
        array_value = matches[0]  # 取第一个匹配结果
        
        assert isinstance(array_value, list), f"字段 {jsonpath_expr} 不是数组类型"
        assert any(match_func(item) for item in array_value), \
            f"数组中没有元素满足条件！JSONPath: {jsonpath_expr}"
        self.logger.info(f"数组元素条件断言成功: {jsonpath_expr}")

    def assert_response_body(self, response, expected_body):
        """
        断言整个响应体
        :param response: 响应对象
        :param expected_body: 期望的完整响应结构
        """
        try:
            actual_body = response.json()
        except json.JSONDecodeError:
            raise AssertionError("响应不是有效的JSON格式")

        # 递归比较响应体
        self._compare_dict(actual_body, expected_body, "$")
        self.logger.info("响应体断言成功")

    def _assert_dict_value(self, actual_dict: Dict, expected_dict: Dict, path: str):
        """断言字典值"""
        for key, expected_value in expected_dict.items():
            assert key in actual_dict, f"字典中未找到键: {key}, 路径: {path}"
            actual_value = actual_dict[key]
            current_path = f"{path}.{key}"
            
            if isinstance(expected_value, dict):
                self._assert_dict_value(actual_value, expected_value, current_path)
            elif isinstance(expected_value, list):
                self._assert_list_value(actual_value, expected_value, current_path)
            else:
                assert actual_value == expected_value, \
                    f"字典值断言失败！路径: {current_path}, 预期: {expected_value}, 实际: {actual_value}"

    def _assert_list_value(self, actual_list: List, expected_list: List, path: str):
        """断言列表值"""
        assert len(actual_list) == len(expected_list), \
            f"列表长度不匹配！路径: {path}, 预期长度: {len(expected_list)}, 实际长度: {len(actual_list)}"
        
        for i, (actual_item, expected_item) in enumerate(zip(actual_list, expected_list)):
            current_path = f"{path}[{i}]"
            
            if isinstance(expected_item, dict):
                self._assert_dict_value(actual_item, expected_item, current_path)
            elif isinstance(expected_item, list):
                self._assert_list_value(actual_item, expected_item, current_path)
            else:
                assert actual_item == expected_item, \
                    f"列表元素断言失败！路径: {current_path}, 预期: {expected_item}, 实际: {actual_item}"

    def _compare_dict(self, actual: dict, expected: dict, path: str):
        """
        递归比较字典结构
        :param actual: 实际值
        :param expected: 期望值
        :param path: 当前字段路径 (使用JSONPath格式)
        """
        # 检查所有期望的键是否存在且值匹配
        for key, exp_value in expected.items():
            current_path = f"{path}.{key}" if path != "$" else f"$.{key}"
            
            # 检查键是否存在
            assert key in actual, f"缺少必需的键！路径: {current_path}"
            actual_value = actual[key]

            # 根据值的类型进行比较
            if isinstance(exp_value, dict):
                assert isinstance(actual_value, dict), \
                    f"类型不匹配！路径: {current_path}, 预期: dict, 实际: {type(actual_value).__name__}"
                self._compare_dict(actual_value, exp_value, current_path)
            elif isinstance(exp_value, list):
                assert isinstance(actual_value, list), \
                    f"类型不匹配！路径: {current_path}, 预期: list, 实际: {type(actual_value).__name__}"
                self._compare_list(actual_value, exp_value, current_path)
            else:
                assert actual_value == exp_value, \
                    f"值不匹配！路径: {current_path}, 预期: {exp_value}, 实际: {actual_value}"

    def _compare_list(self, actual: list, expected: list, path: str):
        """
        比较列表内容
        :param actual: 实际列表
        :param expected: 期望列表
        :param path: 当前字段路径 (使用JSONPath格式)
        """
        assert len(actual) == len(expected), \
            f"列表长度不匹配！路径: {path}, 预期长度: {len(expected)}, 实际长度: {len(actual)}"
        
        for i, (act_item, exp_item) in enumerate(zip(actual, expected)):
            current_path = f"{path}[{i}]"
            
            if isinstance(exp_item, dict):
                assert isinstance(act_item, dict), \
                    f"类型不匹配！路径: {current_path}, 预期: dict, 实际: {type(act_item).__name__}"
                self._compare_dict(act_item, exp_item, current_path)
            elif isinstance(exp_item, list):
                assert isinstance(act_item, list), \
                    f"类型不匹配！路径: {current_path}, 预期: list, 实际: {type(act_item).__name__}"
                self._compare_list(act_item, exp_item, current_path)
            else:
                assert act_item == exp_item, \
                    f"值不匹配！路径: {current_path}, 预期: {exp_item}, 实际: {act_item}" 