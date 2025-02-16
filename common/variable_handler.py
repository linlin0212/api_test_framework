import re
from typing import Any, Dict
from common.yaml_handler import YamlHandler
from common.logger import Logger

class VariableHandler:
    def __init__(self):
        self.yaml_handler = YamlHandler()
        self.logger = Logger()
        self.variables_file = "data/variables.yaml"

    def save_variables(self, response_data: Dict, save_config: Dict) -> None:
        """
        保存接口响应中的变量
        :param response_data: 接口响应数据
        :param save_config: 需要保存的变量配置
        """
        variables = self.yaml_handler.read_yaml(self.variables_file)
        
        for var_name, path in save_config.items():
            try:
                # 从响应中提取数据
                value = self._extract_value(response_data, path)
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

    def _extract_value(self, data: Dict, path: str) -> Any:
        """
        从数据中提取指定路径的值
        :param data: 数据字典
        :param path: 数据路径，如 "data.user.id"
        :return: 提取的值
        """
        keys = path.split('.')
        value = data
        for key in keys:
            if not isinstance(value, dict):
                raise ValueError(f"无法从路径 {path} 提取数据")
            if key not in value:
                raise KeyError(f"键 {key} 不存在")
            value = value[key]
        return value 