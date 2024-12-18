import pytest
from flask_jwt_extended import create_access_token

from src import app as real_app
from tests.tests_tools import (
    request_adding_valid_resource,
    request_invalid_resource_duplicate_key_error,
    request_invalid_resource_validation_error,
    request_unexpected_error,
    request_getting_resources,
    request_getting_resource,
    request_resource_not_found,
    request_resource_not_found_error,
    request_updating_resource,
    request_deleting_resource,
    request_unauthorized_access,
)

URL_PRODUCT = "/product"
URL_PRODUCTS = "/products"
URL_PRODUCT_ID = "/product/507f1f77bcf86cd799439011"
RESOURCE = "producto"

VALID_PRODUCT_DATA = {
    "name": "Cacahuetes",
    "stock": 345,
    "categories": ["snack", "otro"],
    "allergens": ["cacahuete"],
    "brand": "marca",
    "notes": "notas",
}
INVALID_PRODUCT_DATA = {"name": 12345, "stock": 345, "categories": ["snack", "otro"]}
UPDATED_PRODUCT_DATA = {"name": "new_value"}


@pytest.fixture
def app():
    real_app.config["TESTING"] = True
    yield real_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.routes.product_route.coll_products", new=mock_db)
    return mock_db


@pytest.fixture
def auth_header(app):
    with app.app_context():
        access_token = create_access_token(
            identity="test_user", additional_claims={"role": 1}, fresh=True
        )
        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.routes.product_route.get_jwt")


def test_add_product(client, mock_db, auth_header):
    return request_adding_valid_resource(
        client, mock_db, auth_header, URL_PRODUCT, VALID_PRODUCT_DATA
    )


def test_get_products(client, mock_db, auth_header):
    return request_getting_resources(
        client, mock_db, auth_header, URL_PRODUCTS, VALID_PRODUCT_DATA
    )


def test_get_product(client, mock_db, auth_header):
    return request_getting_resource(
        client, mock_db, auth_header, URL_PRODUCT_ID, VALID_PRODUCT_DATA
    )


def test_update_product(client, mock_db, auth_header):
    return request_updating_resource(
        client,
        mock_db,
        auth_header,
        URL_PRODUCT_ID,
        VALID_PRODUCT_DATA,
        UPDATED_PRODUCT_DATA,
    )


def test_delete_product(client, mock_db, auth_header):
    return request_deleting_resource(client, mock_db, auth_header, URL_PRODUCT_ID)


def test_product_route_unauthorized_access(client, auth_header, mock_jwt):
    request_unauthorized_access(
        client, auth_header, mock_jwt, "post", URL_PRODUCT, VALID_PRODUCT_DATA
    )
    request_unauthorized_access(
        client, auth_header, mock_jwt, "get", URL_PRODUCTS, VALID_PRODUCT_DATA
    )
    request_unauthorized_access(
        client, auth_header, mock_jwt, "put", URL_PRODUCT_ID, VALID_PRODUCT_DATA
    )
    request_unauthorized_access(
        client, auth_header, mock_jwt, "delete", URL_PRODUCT_ID, VALID_PRODUCT_DATA
    )


def test_product_route_duplicate_key_error(client, mock_db, auth_header, mocker):
    request_invalid_resource_duplicate_key_error(
        client,
        mock_db,
        auth_header,
        mocker,
        "post",
        URL_PRODUCT,
        VALID_PRODUCT_DATA,
        UPDATED_PRODUCT_DATA,
        "name",
    )
    request_invalid_resource_duplicate_key_error(
        client,
        mock_db,
        auth_header,
        mocker,
        "put",
        URL_PRODUCT_ID,
        VALID_PRODUCT_DATA,
        UPDATED_PRODUCT_DATA,
    )


def test_product_route_validation_error(client, mock_db, auth_header):
    request_invalid_resource_validation_error(
        client, mock_db, auth_header, "post", URL_PRODUCT, INVALID_PRODUCT_DATA
    )
    request_invalid_resource_validation_error(
        client, mock_db, auth_header, "put", URL_PRODUCT_ID, INVALID_PRODUCT_DATA
    )


def test_product_route_unexpected_error(client, mock_db, auth_header):
    request_unexpected_error(client, mock_db, auth_header, "insert_one", URL_PRODUCT)
    request_unexpected_error(client, mock_db, auth_header, "find", URL_PRODUCTS)
    request_unexpected_error(client, mock_db, auth_header, "find_one", URL_PRODUCT_ID)
    request_unexpected_error(
        client, mock_db, auth_header, "find_one_and_update", URL_PRODUCT_ID
    )
    request_unexpected_error(client, mock_db, auth_header, "delete_one", URL_PRODUCT_ID)


def test_product_route_resource_not_found(app, client, mock_db, auth_header):
    request_resource_not_found(app, client, mock_db, auth_header, "get", URL_PRODUCT_ID)
    request_resource_not_found(app, client, mock_db, auth_header, "put", URL_PRODUCT_ID)
    request_resource_not_found(
        app, client, mock_db, auth_header, "delete", URL_PRODUCT_ID
    )


def test_product_route_resource_not_found_error(client, mock_db, auth_header):
    request_resource_not_found_error(
        client,
        mock_db,
        auth_header,
        "get",
        URL_PRODUCT_ID,
        VALID_PRODUCT_DATA,
        RESOURCE,
    )
    request_resource_not_found_error(
        client,
        mock_db,
        auth_header,
        "put",
        URL_PRODUCT_ID,
        VALID_PRODUCT_DATA,
        RESOURCE,
    )
    request_resource_not_found_error(
        client,
        mock_db,
        auth_header,
        "delete",
        URL_PRODUCT_ID,
        VALID_PRODUCT_DATA,
        RESOURCE,
    )
