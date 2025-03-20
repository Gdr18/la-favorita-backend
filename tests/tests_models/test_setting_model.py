import pytest
from pydantic import ValidationError
from pymongo.results import InsertOneResult

from src.models.setting_model import SettingModel


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.settings", new=mock_db)
    return mock_db


def test_setting_valid():
    setting = SettingModel(name="TestSetting", values=["value1", "value2"])
    assert setting.name == "TestSetting"
    assert setting.values == ["value1", "value2"]


@pytest.mark.parametrize(
    "name, values",
    [
        ("", ["value1", "value2"]),
        ("a" * 51, ["value1", "value2"]),
        ("TestSetting", "not_a_list"),
        ("TestSetting", [1, 2, 3]),
        ("TestSetting", ["", "", ""]),
        ("TestSetting", []),
    ],
)
def test_setting_validation_error(name, values):
    with pytest.raises(ValidationError):
        SettingModel(name=name, values=values)


def test_insert_setting(mock_db):
    mock_db.insert_one.return_value = InsertOneResult(inserted_id="507f1f77bcf86cd799439011", acknowledged=True)
    setting = SettingModel(name="TestSetting", values=["value1", "value2"])
    result = setting.insert_setting()

    assert isinstance(result, InsertOneResult)
    assert result.inserted_id == "507f1f77bcf86cd799439011"
    assert result.acknowledged is True


def test_get_settings(mock_db):
    mock_cursor = mock_db.find.return_value
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = [{"name": "TestSetting", "values": ["value1", "value2"]}]

    result = SettingModel.get_settings(1, 10)

    assert isinstance(result, list)
    assert all(isinstance(item, dict) for item in result)
    assert result == [{"name": "TestSetting", "values": ["value1", "value2"]}]


def test_get_setting(mock_db):
    mock_db.find_one.return_value = {"name": "TestSetting", "values": ["value1", "value2"]}
    result = SettingModel.get_setting("507f1f77bcf86cd799439011")

    assert isinstance(result, dict)
    assert result == {"name": "TestSetting", "values": ["value1", "value2"]}
