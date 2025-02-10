import os
import yaml
from typing import Any, Dict, List, Union
from common.logger import Logger

class YamlHandler:
    def __init__(self):
        self.logger = Logger()

    @staticmethod
    def read_yaml(yaml_path: str) -> Union[Dict, List]:
        """
        读取YAML文件
        :param yaml_path: YAML文件路径
        :return: YAML文件内容
        """
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"YAML文件不存在: {yaml_path}")
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"YAML文件格式错误: {str(e)}")
        except Exception as e:
            raise Exception(f"读取YAML文件失败: {str(e)}")

    @staticmethod
    def write_yaml(yaml_path: str, data: Any, mode: str = 'w') -> None:
        """
        写入YAML文件
        :param yaml_path: YAML文件路径
        :param data: 要写入的数据
        :param mode: 写入模式，'w'为覆盖，'a'为追加
        """
        try:
            with open(yaml_path, mode, encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            raise Exception(f"写入YAML文件失败: {str(e)}")

    def merge_yaml(self, yaml_path1: str, yaml_path2: str, output_path: str) -> None:
        """
        合并两个YAML文件
        :param yaml_path1: 第一个YAML文件路径
        :param yaml_path2: 第二个YAML文件路径
        :param output_path: 输出文件路径
        """
        try:
            data1 = self.read_yaml(yaml_path1)
            data2 = self.read_yaml(yaml_path2)
            
            if isinstance(data1, dict) and isinstance(data2, dict):
                merged_data = {**data1, **data2}
            elif isinstance(data1, list) and isinstance(data2, list):
                merged_data = data1 + data2
            else:
                raise TypeError("YAML文件格式不一致，无法合并")
            
            self.write_yaml(output_path, merged_data)
            self.logger.info(f"YAML文件合并成功，已保存至: {output_path}")
        except Exception as e:
            self.logger.error(f"合并YAML文件失败: {str(e)}")
            raise

    def update_yaml(self, yaml_path: str, key_path: str, value: Any) -> None:
        """
        更新YAML文件中的特定值
        :param yaml_path: YAML文件路径
        :param key_path: 键路径，使用点号分隔，如'env.test.base_url'
        :param value: 新值
        """
        try:
            data = self.read_yaml(yaml_path)
            keys = key_path.split('.')
            current = data
            
            # 遍历到最后一个键之前
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 更新最后一个键的值
            current[keys[-1]] = value
            
            self.write_yaml(yaml_path, data)
            self.logger.info(f"已更新YAML文件: {key_path} = {value}")
        except Exception as e:
            self.logger.error(f"更新YAML文件失败: {str(e)}")
            raise

    def get_value(self, yaml_path: str, key_path: str) -> Any:
        """
        获取YAML文件中的特定值
        :param yaml_path: YAML文件路径
        :param key_path: 键路径，使用点号分隔，如'env.test.base_url'
        :return: 对应的值
        """
        try:
            data = self.read_yaml(yaml_path)
            keys = key_path.split('.')
            current = data
            
            for key in keys:
                if not isinstance(current, dict):
                    raise ValueError(f"无法访问键路径: {key_path}")
                if key not in current:
                    raise KeyError(f"键不存在: {key}")
                current = current[key]
            
            return current
        except Exception as e:
            self.logger.error(f"获取YAML值失败: {str(e)}")
            raise

    def validate_yaml_schema(self, yaml_path: str, schema: Dict) -> bool:
        """
        验证YAML文件格式是否符合指定的schema
        :param yaml_path: YAML文件路径
        :param schema: 预期的schema格式
        :return: 是否符合schema
        """
        try:
            data = self.read_yaml(yaml_path)
            return self._validate_schema(data, schema)
        except Exception as e:
            self.logger.error(f"YAML schema验证失败: {str(e)}")
            return False

    def _validate_schema(self, data: Any, schema: Dict) -> bool:
        """
        递归验证数据结构是否符合schema
        """
        if 'type' in schema:
            # 验证数据类型
            expected_type = schema['type']
            if expected_type == 'string':
                return isinstance(data, str)
            elif expected_type == 'number':
                return isinstance(data, (int, float))
            elif expected_type == 'boolean':
                return isinstance(data, bool)
            elif expected_type == 'array':
                if not isinstance(data, list):
                    return False
                if 'items' in schema:
                    return all(self._validate_schema(item, schema['items']) for item in data)
                return True
            elif expected_type == 'object':
                if not isinstance(data, dict):
                    return False
                if 'properties' in schema:
                    return all(
                        key in data and self._validate_schema(data[key], schema['properties'][key])
                        for key in schema['properties']
                    )
                return True
        return True 