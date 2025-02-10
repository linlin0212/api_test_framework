import json
from common.logger import Logger

class Assertions:
    def __init__(self):
        self.logger = Logger()

    def assert_status_code(self, response, expected_code):
        """
        断言响应状态码
        """
        actual_code = response.status_code
        assert actual_code == expected_code, \
            f"断言状态码失败！预期: {expected_code}, 实际: {actual_code}"
        self.logger.info(f"状态码断言成功: {actual_code}")

    def assert_contains_field(self, response, field):
        """
        断言响应包含指定字段
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            raise AssertionError("响应不是有效的JSON格式")

        assert self._check_field_exists(response_data, field), \
            f"响应中未找到字段: {field}"
        self.logger.info(f"字段存在性断言成功: {field}")

    def assert_field_value(self, response, field_path, expected_value):
        """
        断言字段值
        :param field_path: 字段路径，支持嵌套，如 'data.user.name'
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            raise AssertionError("响应不是有效的JSON格式")

        actual_value = self._get_field_value(response_data, field_path)
        assert actual_value == expected_value, \
            f"字段值断言失败！字段: {field_path}, 预期: {expected_value}, 实际: {actual_value}"
        self.logger.info(f"字段值断言成功: {field_path} = {actual_value}")

    def _check_field_exists(self, data, field):
        """检查字段是否存在（支持嵌套字段）"""
        fields = field.split('.')
        current = data
        
        for f in fields:
            if isinstance(current, dict):
                if f not in current:
                    return False
                current = current[f]
            else:
                return False
        return True

    def _get_field_value(self, data, field_path):
        """获取字段值（支持嵌套字段）"""
        fields = field_path.split('.')
        current = data
        
        for f in fields:
            if isinstance(current, dict):
                if f not in current:
                    raise AssertionError(f"字段不存在: {field_path}")
                current = current[f]
            else:
                raise AssertionError(f"无法访问字段: {field_path}")
        return current 