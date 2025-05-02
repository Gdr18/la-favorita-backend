import pytest
import pendulum
from flask_jwt_extended import create_access_token

from src import app as real_app
from tests.test_helpers import (
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

URL_REVOKED_TOKEN = "/revoked_token"
URL_REVOKED_TOKENS = "/revoked_tokens"
URL_REVOKED_TOKEN_ID = "/revoked_token/507f1f77bcf86cd799439011"
RESOURCE = "token revocado"

VALID_REVOKED_TOKEN_DATA = {
    "exp": 1919068218,
    "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
}
INVALID_REVOKED_TOKEN_DATA = {
    "exp": 1919068218666,
    "jti": "bb53e63744-8627-457c-840f-6cae52a12e8b",
}
UPDATED_REVOKED_TOKEN_DATA = {"exp": 1919068250}


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
    mocker.patch("src.routes.revoked_token_route.coll_revoked_tokens", new=mock_db)
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
    return mocker.patch("src.routes.revoked_token_route.get_jwt")


def test_add_revoked_token(client, mock_db, auth_header):
    return request_adding_valid_resource(
        client, mock_db, auth_header, URL_REVOKED_TOKEN, VALID_REVOKED_TOKEN_DATA
    )


def test_get_revoked_tokens(client, mock_db, auth_header):
    return request_getting_resources(
        client, mock_db, auth_header, URL_REVOKED_TOKENS, VALID_REVOKED_TOKEN_DATA
    )


def test_get_revoked_token(client, mock_db, auth_header):
    return request_getting_resource(
        client, mock_db, auth_header, URL_REVOKED_TOKEN_ID, VALID_REVOKED_TOKEN_DATA
    )


def test_update_revoked_token(client, mock_db, auth_header):
    return request_updating_resource(
        client,
        mock_db,
        auth_header,
        URL_REVOKED_TOKEN_ID,
        VALID_REVOKED_TOKEN_DATA,
        UPDATED_REVOKED_TOKEN_DATA,
    )


def test_delete_revoked_token(client, mock_db, auth_header):
    return request_deleting_resource(client, mock_db, auth_header, URL_REVOKED_TOKEN_ID)


def test_revoked_token_route_unauthorized_access(client, auth_header, mock_jwt):
    request_unauthorized_access(
        client,
        auth_header,
        mock_jwt,
        "post",
        URL_REVOKED_TOKEN,
        VALID_REVOKED_TOKEN_DATA,
    )
    request_unauthorized_access(
        client,
        auth_header,
        mock_jwt,
        "get",
        URL_REVOKED_TOKENS,
        VALID_REVOKED_TOKEN_DATA,
    )
    request_unauthorized_access(
        client,
        auth_header,
        mock_jwt,
        "put",
        URL_REVOKED_TOKEN_ID,
        VALID_REVOKED_TOKEN_DATA,
    )
    request_unauthorized_access(
        client,
        auth_header,
        mock_jwt,
        "delete",
        URL_REVOKED_TOKEN_ID,
        VALID_REVOKED_TOKEN_DATA,
    )


def test_revoked_token_route_duplicate_key_error(client, mock_db, auth_header, mocker):
    request_invalid_resource_duplicate_key_error(
        client,
        mock_db,
        auth_header,
        mocker,
        "post",
        URL_REVOKED_TOKEN,
        VALID_REVOKED_TOKEN_DATA,
        UPDATED_REVOKED_TOKEN_DATA,
        "name",
    )
    request_invalid_resource_duplicate_key_error(
        client,
        mock_db,
        auth_header,
        mocker,
        "put",
        URL_REVOKED_TOKEN_ID,
        VALID_REVOKED_TOKEN_DATA,
        UPDATED_REVOKED_TOKEN_DATA,
    )


def test_revoked_token_route_validation_error(client, mock_db, auth_header):
    request_invalid_resource_validation_error(
        client,
        mock_db,
        auth_header,
        "post",
        URL_REVOKED_TOKEN,
        INVALID_REVOKED_TOKEN_DATA,
    )
    request_invalid_resource_validation_error(
        client,
        mock_db,
        auth_header,
        "put",
        URL_REVOKED_TOKEN_ID,
        INVALID_REVOKED_TOKEN_DATA,
    )


def test_revoked_token_route_unexpected_error(client, mock_db, auth_header):
    request_unexpected_error(
        client, mock_db, auth_header, "insert_one", URL_REVOKED_TOKEN
    )
    request_unexpected_error(client, mock_db, auth_header, "find", URL_REVOKED_TOKENS)
    request_unexpected_error(
        client, mock_db, auth_header, "find_one", URL_REVOKED_TOKEN_ID
    )
    request_unexpected_error(
        client, mock_db, auth_header, "find_one_and_update", URL_REVOKED_TOKEN_ID
    )
    request_unexpected_error(
        client, mock_db, auth_header, "delete_one", URL_REVOKED_TOKEN_ID
    )


def test_revoked_token_route_resource_not_found(app, client, mock_db, auth_header):
    request_resource_not_found(
        app, client, mock_db, auth_header, "get", URL_REVOKED_TOKEN_ID
    )
    request_resource_not_found(
        app, client, mock_db, auth_header, "put", URL_REVOKED_TOKEN_ID
    )
    request_resource_not_found(
        app, client, mock_db, auth_header, "delete", URL_REVOKED_TOKEN_ID
    )


def test_revoked_token_route_resource_not_found_error(client, mock_db, auth_header):
    request_resource_not_found_error(
        client,
        mock_db,
        auth_header,
        "get",
        URL_REVOKED_TOKEN_ID,
        VALID_REVOKED_TOKEN_DATA,
        RESOURCE,
    )
    request_resource_not_found_error(
        client,
        mock_db,
        auth_header,
        "put",
        URL_REVOKED_TOKEN_ID,
        VALID_REVOKED_TOKEN_DATA,
        RESOURCE,
    )
    request_resource_not_found_error(
        client,
        mock_db,
        auth_header,
        "delete",
        URL_REVOKED_TOKEN_ID,
        VALID_REVOKED_TOKEN_DATA,
        RESOURCE,
    )
