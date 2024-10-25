import pytest
from flask_jwt_extended import create_access_token

from src import app as real_app
from tests.tests_tools import request_adding_valid_resource, request_invalid_resource_duplicate_key_error, request_invalid_resource_validation_error, request_unexpected_error, request_getting_resources, request_getting_resource, request_resource_not_found, request_resource_not_found_error, request_updating_resource, request_deleting_resource, request_unauthorized_access, request_unauthorized_set

URL_USER = '/user'
URL_USERS = '/users'
URL_USER_ID = '/user/507f1f77bcf86cd799439011'
RESOURCE = 'usuario'

VALID_USER_DATA = {"name": "John Doe", "email": "john.doe@example.com", "password": "ValidPass123!"}
VALID_USER_DATA_ROLE = {**VALID_USER_DATA, "role": 2}
INVALID_USER_DATA = {"name": 12345, "email": "john.doe", "password": "invalid_pass"}
UPDATED_USER_DATA = {'name': 'new_value'}
UPDATED_USER_DATA_ROLE = {"role": 3}


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
    mocker.patch('src.routes.user_route.coll_users', new=mock_db)
    return mock_db


@pytest.fixture
def auth_header(app):
    with app.app_context():
        access_token = create_access_token(identity='507f1f77bcf86cd799439011', additional_claims={'role': 1}, fresh=True)
        return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch('src.routes.user_route.get_jwt')


def test_add_user(client, mock_db, auth_header):
    return request_adding_valid_resource(client, mock_db, auth_header, URL_USER, VALID_USER_DATA)


def test_get_users(client, mock_db, auth_header):
    return request_getting_resources(client, mock_db, auth_header, URL_USERS, VALID_USER_DATA)


def test_get_user(client, mock_db, auth_header):
    return request_getting_resource(client, mock_db, auth_header, URL_USER_ID, VALID_USER_DATA)


def test_update_user(client, mock_db, auth_header):
    return request_updating_resource(client, mock_db, auth_header, URL_USER_ID, VALID_USER_DATA, UPDATED_USER_DATA)


def test_delete_user(client, mock_db, auth_header):
    return request_deleting_resource(client, mock_db, auth_header, URL_USER_ID)


def test_user_route_unauthorized_access(client, auth_header, mock_jwt):
    request_unauthorized_access(client, auth_header, mock_jwt, 'get', URL_USERS, {**VALID_USER_DATA, "role": 3})
    request_unauthorized_access(client, auth_header, mock_jwt, 'put', URL_USER_ID, {**VALID_USER_DATA, "role": 3})
    request_unauthorized_access(client, auth_header, mock_jwt, 'delete', URL_USER_ID, {**VALID_USER_DATA, "role": 3})


def test_user_route_unauthorized_set(client, mock_db, auth_header, mock_jwt):
    request_unauthorized_set(client, mock_db, auth_header, mock_jwt, 'post', URL_USER, VALID_USER_DATA_ROLE)
    request_unauthorized_set(client, mock_db, auth_header, mock_jwt, 'put', URL_USER_ID, VALID_USER_DATA_ROLE, UPDATED_USER_DATA_ROLE)


def test_user_route_duplicate_key_error(client, mock_db, auth_header, mocker):
    request_invalid_resource_duplicate_key_error(client, mock_db, auth_header, mocker, 'post', URL_USER, VALID_USER_DATA, UPDATED_USER_DATA, 'name')
    request_invalid_resource_duplicate_key_error(client, mock_db, auth_header, mocker, 'put', URL_USER_ID, VALID_USER_DATA, UPDATED_USER_DATA)


def test_user_route_validation_error(client, mock_db, auth_header):
    request_invalid_resource_validation_error(client, mock_db, auth_header, 'post', URL_USER, INVALID_USER_DATA)
    request_invalid_resource_validation_error(client, mock_db, auth_header, 'put', URL_USER_ID, INVALID_USER_DATA)


def test_user_route_unexpected_error(client, mock_db, auth_header):
    request_unexpected_error(client, mock_db, auth_header, 'insert_one', URL_USER)
    request_unexpected_error(client, mock_db, auth_header, 'find', URL_USERS)
    request_unexpected_error(client, mock_db, auth_header, 'find_one', URL_USER_ID)
    request_unexpected_error(client, mock_db, auth_header, 'find_one_and_update', URL_USER_ID)
    request_unexpected_error(client, mock_db, auth_header, 'delete_one', URL_USER_ID)


def test_user_route_resource_not_found(app, client, mock_db, auth_header):
    request_resource_not_found(app, client, mock_db, auth_header, 'get', URL_USER_ID)
    request_resource_not_found(app, client, mock_db, auth_header, 'put', URL_USER_ID)
    request_resource_not_found(app, client, mock_db, auth_header, 'delete', URL_USER_ID)


def test_user_route_resource_not_found_error(client, mock_db, auth_header):
    request_resource_not_found_error(client, mock_db, auth_header, 'get', URL_USER_ID, VALID_USER_DATA, RESOURCE)
    request_resource_not_found_error(client, mock_db, auth_header, 'put', URL_USER_ID, VALID_USER_DATA, RESOURCE)
    request_resource_not_found_error(client, mock_db, auth_header, 'delete', URL_USER_ID, VALID_USER_DATA, RESOURCE)
