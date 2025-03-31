import pytest
import allure
from testcases.test_base import TestBase
from common.yaml_handler import YamlHandler

@allure.epic("API自动化测试")
@allure.feature("场景测试")
class TestScenarios(TestBase):
    @allure.story("场景用例")
    @pytest.mark.scenario
    @pytest.mark.parametrize("scenario", YamlHandler.read_yaml("data/test_data.yaml")["scenario_cases"])
    def test_scenario(self, scenario):
        """场景测试用例"""
        allure.dynamic.title(scenario["scenario_name"])
        allure.dynamic.description(scenario.get("description", ""))

        # 遍历场景中的每个步骤
        for step_index, step in enumerate(scenario["steps"], 1):
            step_name = f"步骤 {step_index}: {step['step_name']}"
            self.execute_test_step(step, step_name) 