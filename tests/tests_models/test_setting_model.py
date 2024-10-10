import pytest
from pydantic import ValidationError
from src.models.setting_model import SettingModel


def test_setting_model_valid():
    setting = SettingModel(name="TestSetting", values=["value1", "value2"])
    assert setting.name == "TestSetting"
    assert setting.values == ["value1", "value2"]


def test_setting_model_invalid_name_too_short():
    with pytest.raises(ValidationError):
        SettingModel(name="", values=["value1", "value2"])


def test_setting_model_invalid_name_too_long():
    with pytest.raises(ValidationError):
        SettingModel(name="a" * 51, values=["value1", "value2"])


def test_setting_model_invalid_values_not_list():
    with pytest.raises(ValidationError):
        SettingModel(name="TestSetting", values="not_a_list")


def test_setting_model_invalid_values_list_of_non_strings():
    with pytest.raises(ValidationError):
        SettingModel(name="TestSetting", values=[1, 2, 3])


def test_setting_model_invalid_values_list_of_empty_strings():
    with pytest.raises(ValidationError):
        SettingModel(name="TestSetting", values=["", "", ""])


def test_setting_model_invalid_values_empty_list():
    with pytest.raises(ValidationError):
        SettingModel(name="TestSetting", values=[])


def test_setting_model_to_dict():
    setting = SettingModel(name="TestSetting", values=["value1", "value2"])
    setting_dict = setting.to_dict()
    assert isinstance(setting_dict, dict)
    assert setting_dict["name"] == "TestSetting"
    assert setting_dict["values"] == ["value1", "value2"]
