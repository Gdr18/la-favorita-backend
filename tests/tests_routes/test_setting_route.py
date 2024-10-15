import pytest

from src import app as real_app
from tests.tests_tools import request_adding_valid_resource, request_invalid_resource_duplicate_key_error, request_invalid_resource_validation_error, request_unexpected_error, request_getting_resources, request_getting_resource, request_resource_not_found, request_resource_not_found_error, request_updating_resource, request_deleting_resource


ROUTE_SETTING = 'src.routes.setting_route.coll_settings'
URL_SETTING = '/setting'
URL_SETTINGS = '/settings'
URL_SETTING_ID = '/setting/507f1f77bcf86cd799439011'
RESOURCE = 'configuración'


@pytest.fixture
def app():
    real_app.config['TESTING'] = True
    yield real_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch(ROUTE_SETTING, new=mock_db)
    return mock_db


@pytest.fixture
def valid_setting_data():
    return {'name': 'test', 'values': ['value1', 'value2']}


@pytest.fixture
def invalid_setting_data():
    return {'name': 12345, 'values': ['value1', 'value2']}


@pytest.fixture
def updated_setting_data():
    return {'name': 'new_value'}


def test_add_setting(client, mock_db, valid_setting_data):
    return request_adding_valid_resource(client, mock_db, URL_SETTING, valid_setting_data)


def test_add_setting_duplicate_key(client, mock_db, mocker, valid_setting_data, updated_setting_data):
    return request_invalid_resource_duplicate_key_error(client, mock_db, mocker, 'post', URL_SETTING, valid_setting_data, updated_setting_data, 'name')


def test_add_setting_validation_error(client, mock_db, invalid_setting_data):
    return request_invalid_resource_validation_error(client, mock_db, 'post', URL_SETTING, invalid_setting_data)


def test_add_setting_unexpected_error(client, mock_db):
    return request_unexpected_error(client, mock_db, 'insert_one', URL_SETTING)


def test_get_settings(client, mock_db, valid_setting_data):
    return request_getting_resources(client, mock_db, URL_SETTINGS, valid_setting_data)


def test_get_settings_unexpected_error(client, mock_db):
    return request_unexpected_error(client, mock_db, 'find', URL_SETTINGS)


def test_get_setting(client, mock_db, valid_setting_data):
    return request_getting_resource(client, mock_db, URL_SETTING_ID, valid_setting_data)


def test_get_setting_resource_not_found(app, client, mock_db):
    return request_resource_not_found(app, client, mock_db, 'get', URL_SETTING_ID)


def test_get_setting_resource_not_found_error(client, mock_db, valid_setting_data):
    return request_resource_not_found_error(client, mock_db, 'get', URL_SETTING_ID, valid_setting_data, RESOURCE)


def test_get_setting_unexpected_error(client, mock_db):
    return request_unexpected_error(client, mock_db, 'find_one', URL_SETTING_ID)


def test_update_setting(client, mock_db, updated_setting_data, valid_setting_data):
    return request_updating_resource(client, mock_db, URL_SETTING_ID, valid_setting_data, updated_setting_data)


def test_update_setting_resource_not_found(app, client, mock_db):
    return request_resource_not_found(app, client, mock_db, 'put', URL_SETTING_ID)


def test_update_setting_resource_not_found_error(client, mock_db, valid_setting_data):
    return request_resource_not_found_error(client, mock_db, 'put', URL_SETTING_ID, valid_setting_data, RESOURCE)


def test_update_setting_duplicate_key(client, mock_db, mocker, updated_setting_data, valid_setting_data):
    return request_invalid_resource_duplicate_key_error(client, mock_db, mocker, 'put', URL_SETTING_ID, valid_setting_data, updated_setting_data)


def test_update_setting_validation_error(client, mock_db, invalid_setting_data):
    return request_invalid_resource_validation_error(client, mock_db, 'put', URL_SETTING_ID, invalid_setting_data)


def test_update_setting_unexpected_error(client, mock_db):
    return request_unexpected_error(client, mock_db, 'find_one_and_update', URL_SETTING_ID)


def test_delete_setting(client, mock_db):
    return request_deleting_resource(client, mock_db, URL_SETTING_ID)


def test_delete_setting_resource_not_found(app, client, mock_db):
    return request_resource_not_found(app, client, mock_db, 'delete', URL_SETTING_ID)


def test_delete_setting_resource_not_found_error(client, mock_db, valid_setting_data):
    return request_resource_not_found_error(client, mock_db, 'delete', URL_SETTING_ID, valid_setting_data, RESOURCE)


def test_delete_setting_unexpected_error(client, mock_db,):
    return request_unexpected_error(client, mock_db, 'delete_one', URL_SETTING_ID)
