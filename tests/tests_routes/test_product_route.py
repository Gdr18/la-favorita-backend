import pytest
from flask_jwt_extended import create_access_token

from src import app as real_app
from tests.tests_tools import request_adding_valid_resource, request_invalid_resource_duplicate_key_error, request_invalid_resource_validation_error, request_unexpected_error, request_getting_resources, request_getting_resource, request_resource_not_found, request_resource_not_found_error, request_updating_resource, request_deleting_resource


URL_PRODUCT = '/product'
URL_PRODUCTS = '/products'
URL_PRODUCT_ID = '/product/507f1f77bcf86cd799439011'
RESOURCE = 'producto'


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
    mocker.patch('src.routes.product_route.coll_products', new=mock_db)
    return mock_db


@pytest.fixture
def auth_header(app):
    with app.app_context():
        access_token = create_access_token(identity='test_user', additional_claims={'role': 1}, fresh=True)
        return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def valid_product_data():
    return {"name": "Cacahuetes", "stock": 345, "categories": ["snack", "otro"], "allergens": ["cacahuete"], "brand": "marca", "notes": "notas"}


@pytest.fixture
def invalid_product_data():
    return {'name': 12345, 'stock': 345, 'categories': ["snack", "otro"]}


@pytest.fixture
def updated_product_data():
    return {'name': 'new_value'}


def test_add_product(client, mock_db, auth_header, valid_product_data):
    return request_adding_valid_resource(client, mock_db, auth_header, URL_PRODUCT, valid_product_data)


def test_add_product_duplicate_key(client, mock_db, auth_header, mocker, valid_product_data, updated_product_data):
    return request_invalid_resource_duplicate_key_error(client, mock_db, auth_header, mocker, 'post', URL_PRODUCT, valid_product_data, updated_product_data, 'name')


def test_add_product_validation_error(client, mock_db, auth_header, invalid_product_data):
    return request_invalid_resource_validation_error(client, mock_db, auth_header, 'post', URL_PRODUCT, invalid_product_data)


def test_add_product_unexpected_error(client, mock_db, auth_header):
    return request_unexpected_error(client, mock_db, auth_header, 'insert_one', URL_PRODUCT)


def test_get_products(client, mock_db, auth_header, valid_product_data):
    return request_getting_resources(client, mock_db, auth_header, URL_PRODUCTS, valid_product_data)


def test_get_products_unexpected_error(client, mock_db, auth_header):
    return request_unexpected_error(client, mock_db, auth_header, 'find', URL_PRODUCTS)


def test_get_product(client, mock_db, auth_header, valid_product_data):
    return request_getting_resource(client, mock_db, auth_header, URL_PRODUCT_ID, valid_product_data)


def test_get_product_resource_not_found(app, client, mock_db, auth_header):
    return request_resource_not_found(app, client, mock_db, auth_header, 'get', URL_PRODUCT_ID)


def test_get_product_resource_not_found_error(client, mock_db, auth_header, valid_product_data):
    return request_resource_not_found_error(client, mock_db, auth_header, 'get', URL_PRODUCT_ID, valid_product_data, RESOURCE)


def test_get_product_unexpected_error(client, mock_db, auth_header):
    return request_unexpected_error(client, mock_db, auth_header, 'find_one', URL_PRODUCT_ID)


def test_update_product(client, mock_db, auth_header, updated_product_data, valid_product_data):
    return request_updating_resource(client, mock_db, auth_header, URL_PRODUCT_ID, valid_product_data, updated_product_data)


def test_update_product_resource_not_found(app, client, mock_db, auth_header,):
    return request_resource_not_found(app, client, mock_db, auth_header, 'put', URL_PRODUCT_ID)


def test_update_product_resource_not_found_error(client, mock_db, auth_header, valid_product_data):
    return request_resource_not_found_error(client, mock_db, auth_header, 'put', URL_PRODUCT_ID, valid_product_data, RESOURCE)


def test_update_product_duplicate_key(client, mock_db, auth_header, mocker, updated_product_data, valid_product_data):
    return request_invalid_resource_duplicate_key_error(client, mock_db, auth_header, mocker, 'put', URL_PRODUCT_ID, valid_product_data, updated_product_data)


def test_update_product_validation_error(client, mock_db, auth_header, invalid_product_data):
    return request_invalid_resource_validation_error(client, mock_db, auth_header, 'put', URL_PRODUCT_ID, invalid_product_data)


def test_update_product_unexpected_error(client, mock_db, auth_header):
    return request_unexpected_error(client, mock_db, auth_header, 'find_one_and_update', URL_PRODUCT_ID)


def test_delete_product(client, mock_db, auth_header):
    return request_deleting_resource(client, mock_db, auth_header, URL_PRODUCT_ID)


def test_delete_product_resource_not_found(app, client, mock_db, auth_header):
    return request_resource_not_found(app, client, mock_db, auth_header, 'delete', URL_PRODUCT_ID)


def test_delete_product_resource_not_found_error(client, mock_db, auth_header, valid_product_data):
    return request_resource_not_found_error(client, mock_db, auth_header, 'delete', URL_PRODUCT_ID, valid_product_data, RESOURCE)


def test_delete_product_unexpected_error(client, mock_db, auth_header):
    return request_unexpected_error(client, mock_db, auth_header, 'delete_one', URL_PRODUCT_ID)
