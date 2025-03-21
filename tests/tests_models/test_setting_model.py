import pytest
from pydantic import ValidationError

from src.models.setting_model import SettingModel

USER_ID = "507f1f77bcf86cd799439011"
SETTING_DATA = {"name": "TestSetting", "values": ["value1", "value2"]}


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.settings", new=mock_db)
    return mock_db


def test_setting_valid():
    setting = SettingModel(**SETTING_DATA)
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
    mock_db.insert_one.return_value.inserted_id = USER_ID
    setting = SettingModel(**SETTING_DATA)
    result = setting.insert_setting()

    assert result.inserted_id == USER_ID


def test_get_settings(mock_db):
    mock_cursor = mock_db.find.return_value
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = [SETTING_DATA]

    result = SettingModel.get_settings(1, 10)

    assert isinstance(result, list)
    assert all(isinstance(item, dict) for item in result)
    assert result == [SETTING_DATA]


def test_get_setting(mock_db):
    mock_db.find_one.return_value = SETTING_DATA
    result = SettingModel.get_setting(USER_ID)

    assert isinstance(result, dict)
    assert result == SETTING_DATA


def test_update_setting(mock_db):
    setting = SettingModel(name="TestSetting2", values=SETTING_DATA["values"])
    mock_db.find_one_and_update.return_value = {**SETTING_DATA, "name": "TestSetting2"}

    result = setting.update_setting(USER_ID)

    assert isinstance(result, dict)
    assert result == setting.__dict__


def test_delete_setting(mock_db):
    mock_db.delete_one.return_value.deleted_count = 1

    result = SettingModel.delete_setting(USER_ID)

    assert result.deleted_count == 1
