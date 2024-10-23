import pytest
from flask_jwt_extended import create_access_token

from src import app as real_app
from tests.tests_tools import request_adding_valid_resource, request_invalid_resource_duplicate_key_error, request_invalid_resource_validation_error, request_unexpected_error, request_getting_resources, request_getting_resource, request_resource_not_found, request_resource_not_found_error, request_updating_resource, request_deleting_resource, request_unauthorized_access


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
def auth_header(app):
    with app.app_context():
        access_token = create_access_token(identity='test_user', additional_claims={'role': 1}, fresh=True)
        return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch('src.routes.setting_route.get_jwt')


@pytest.fixture
def valid_setting_data():
    return {'name': 'test', 'values': ['value1', 'value2']}


@pytest.fixture
def invalid_setting_data():
    return {'name': 12345, 'values': ['value1', 'value2']}


@pytest.fixture
def updated_setting_data():
    return {'name': 'new_value'}


def test_add_setting(client, mock_db, auth_header, valid_setting_data):
    return request_adding_valid_resource(client, mock_db, auth_header, URL_SETTING, valid_setting_data)


def test_get_settings(client, mock_db, auth_header, valid_setting_data):
    return request_getting_resources(client, mock_db, auth_header, URL_SETTINGS, valid_setting_data)


def test_get_setting(client, mock_db, auth_header, valid_setting_data):
    return request_getting_resource(client, mock_db, auth_header, URL_SETTING_ID, valid_setting_data)


def test_update_setting(client, mock_db, auth_header, updated_setting_data, valid_setting_data):
    return request_updating_resource(client, mock_db, auth_header, URL_SETTING_ID, valid_setting_data, updated_setting_data)


def test_delete_setting(client, mock_db, auth_header):
    return request_deleting_resource(client, mock_db, auth_header, URL_SETTING_ID)


def test_setting_route_unauthorized_access(client, auth_header, mock_jwt, valid_setting_data):
    request_unauthorized_access(client, auth_header, mock_jwt, 'post', URL_SETTING, valid_setting_data)
    request_unauthorized_access(client, auth_header, mock_jwt, 'get', URL_SETTINGS, valid_setting_data)
    request_unauthorized_access(client, auth_header, mock_jwt, 'put', URL_SETTING_ID, valid_setting_data)
    request_unauthorized_access(client, auth_header, mock_jwt, 'delete', URL_SETTING_ID, valid_setting_data)


def test_setting_route_duplicate_key_error(client, mock_db, auth_header, mocker, valid_setting_data, updated_setting_data):
    request_invalid_resource_duplicate_key_error(client, mock_db, auth_header, mocker, 'post', URL_SETTING, valid_setting_data, updated_setting_data, 'name')
    request_invalid_resource_duplicate_key_error(client, mock_db, auth_header, mocker, 'put', URL_SETTING_ID, valid_setting_data, updated_setting_data)


def test_setting_route_validation_error(client, mock_db, auth_header, invalid_setting_data):
    request_invalid_resource_validation_error(client, mock_db, auth_header, 'post', URL_SETTING, invalid_setting_data)
    request_invalid_resource_validation_error(client, mock_db, auth_header, 'put', URL_SETTING_ID, invalid_setting_data)


def test_setting_route_unexpected_error(client, mock_db, auth_header):
    request_unexpected_error(client, mock_db, auth_header, 'insert_one', URL_SETTING)
    request_unexpected_error(client, mock_db, auth_header, 'find', URL_SETTINGS)
    request_unexpected_error(client, mock_db, auth_header, 'find_one', URL_SETTING_ID)
    request_unexpected_error(client, mock_db, auth_header, 'find_one_and_update', URL_SETTING_ID)
    request_unexpected_error(client, mock_db, auth_header, 'delete_one', URL_SETTING_ID)


def test_setting_route_resource_not_found(app, client, mock_db, auth_header):
    request_resource_not_found(app, client, mock_db, auth_header, 'get', URL_SETTING_ID)
    request_resource_not_found(app, client, mock_db, auth_header, 'put', URL_SETTING_ID)
    request_resource_not_found(app, client, mock_db, auth_header, 'delete', URL_SETTING_ID)


def test_setting_route_resource_not_found_error(client, mock_db, auth_header, valid_setting_data):
    request_resource_not_found_error(client, mock_db, auth_header, 'get', URL_SETTING_ID, valid_setting_data, RESOURCE)
    request_resource_not_found_error(client, mock_db, auth_header, 'put', URL_SETTING_ID, valid_setting_data, RESOURCE)
    request_resource_not_found_error(client, mock_db, auth_header, 'delete', URL_SETTING_ID, valid_setting_data, RESOURCE)
