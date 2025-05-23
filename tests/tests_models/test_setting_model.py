import pytest
from pydantic import ValidationError

from src.models.setting_model import SettingModel
from tests.test_helpers import (
    assert_insert_document_template,
    assert_get_all_documents_template,
    assert_get_document_by_id_template,
    assert_update_document_template,
    assert_delete_document_template,
)

ID = "507f1f77bcf86cd799439011"
VALID_DATA = {"name": "TestSetting", "values": ["value1", "value2"]}


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_service.db.settings", new=mock_db)
    return mock_db


def test_setting_valid():
    setting = SettingModel(**VALID_DATA)
    assert isinstance(setting.name, str) and 0 < len(setting.name) < 51
    assert (
        isinstance(setting.values, list)
        and all(isinstance(item, str) for item in setting.values)
        and len(setting.values) >= 1
    )


@pytest.mark.parametrize(
    "name, values",
    [
        ("", VALID_DATA["values"]),
        ("a" * 51, VALID_DATA["values"]),
        (VALID_DATA["name"], "not_a_list"),
        (VALID_DATA["name"], [1, 2, 3]),
        (VALID_DATA["name"], ["", "", ""]),
        (VALID_DATA["name"], []),
    ],
)
def test_setting_validation_error(name, values):
    with pytest.raises(ValidationError):
        SettingModel(name=name, values=values)


def test_insert_setting(mock_db):
    return assert_insert_document_template(
        mock_db, SettingModel(**VALID_DATA).insert_setting
    )


def test_get_settings(mock_db):
    return assert_get_all_documents_template(
        mock_db, SettingModel.get_settings, [VALID_DATA]
    )


def test_get_setting(mock_db):
    return assert_get_document_by_id_template(
        mock_db, SettingModel.get_setting, VALID_DATA
    )


def test_update_setting(mock_db):
    new_data = {**VALID_DATA, "name": "TestSetting2"}
    setting_object = SettingModel(**new_data)
    return assert_update_document_template(
        mock_db,
        setting_object.update_setting,
        new_data,
    )


def test_delete_setting(mock_db):
    return assert_delete_document_template(mock_db, SettingModel.delete_setting)
