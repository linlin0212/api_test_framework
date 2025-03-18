import re
from typing import Any, Dict
from jsonpath_ng import parse
from common.yaml_handler import YamlHandler
from common.logger import Logger

class VariableHandler:
    def __init__(self):
        self.yaml_handler = YamlHandler()
        self.logger = Logger()
        self.variables_file = "data/variables.yaml"

    def save_variables(self, response_data: Dict, save_config: Dict) -> None:
        """
        保存接口响应中的变量 (支持JSONPath)
        :param response_data: 接口响应数据
        :param save_config: 需要保存的变量配置
        """
        variables = self.yaml_handler.read_yaml(self.variables_file)
        
        for var_name, path in save_config.items():
            try:
                # 检查路径格式
                if path.startswith('$'):
                    # JSONPath格式
                    value = self._extract_jsonpath_value(response_data, path)
                else:
                    # 传统点号分隔格式，为兼容性保留
                    value = self._extract_dot_value(response_data, path)
                
                # 更新变量
                variables['variables'][var_name] = value
                self.logger.info(f"保存变量: {var_name} = {value}")
            except Exception as e:
                self.logger.error(f"保存变量 {var_name} 失败: {str(e)}")
                raise

        # 写入文件
        self.yaml_handler.write_yaml(self.variables_file, variables)

    def replace_variables(self, data: Any) -> Any:
        """
        替换数据中的变量占位符
        :param data: 要处理的数据
        :return: 替换后的数据
        """
        if isinstance(data, str):
            return self._replace_string_variables(data)
        elif isinstance(data, dict):
            return {k: self.replace_variables(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.replace_variables(item) for item in data]
        return data

    def _replace_string_variables(self, text: str) -> str:
        """
        替换字符串中的变量占位符
        :param text: 要处理的字符串
        :return: 替换后的字符串
        """
        if not isinstance(text, str):
            return text

        variables = self.yaml_handler.read_yaml(self.variables_file)['variables']
        pattern = r'\${(\w+)}'
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name not in variables:
                self.logger.warning(f"变量 {var_name} 未找到")
                return match.group(0)
            return str(variables[var_name])

        return re.sub(pattern, replace_var, text)

    def _extract_jsonpath_value(self, data: Dict, jsonpath_expr: str) -> Any:
        """
        使用JSONPath从数据中提取值
        :param data: 数据字典
        :param jsonpath_expr: JSONPath表达式，如 "$.data.user.id"
        :return: 提取的值
        """
        jsonpath_expr = parse(jsonpath_expr)
        matches = [match.value for match in jsonpath_expr.find(data)]
        
        if not matches:
            raise ValueError(f"JSONPath '{jsonpath_expr}' 未匹配到任何内容")
        
        # 通常返回第一个匹配结果
        return matches[0]

    def _extract_dot_value(self, data: Dict, path: str) -> Any:
        """
        使用点号分隔路径从数据中提取值 (向后兼容)
        :param data: 数据字典
        :param path: 数据路径，如 "data.user.id"
        :return: 提取的值
        """
        keys = path.split('.')
        value = data
        for key in keys:
            if not isinstance(value, dict):
                raise ValueError(f"无法从路径 {path} 提取数据，'{key}' 处不是字典")
            if key not in value:
                raise KeyError(f"键 '{key}' 不存在，路径: {path}")
            value = value[key]
        return value 