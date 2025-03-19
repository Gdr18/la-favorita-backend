import pytest

from src.app import app as real_app
from src.services.security_service import (
    revoke_access_token,
    check_if_token_revoked,
    revoked_token_callback,
    expired_token_callback,
    unauthorized_callback,
)
from tests.tests_tools import validate_success_response_generic, validate_error_response_specific

VALID_JWT = {"jti": "bb53e637-8627-457c-840f-6cae52a12e8b", "exp": 1919068218}


@pytest.fixture
def app():
    real_app.config["TESTING"] = True
    return real_app


@pytest.fixture
def mock_db(mocker):
    return mocker.patch("src.services.auth_service.db")


@pytest.fixture
def mock_bcrypt(mocker):
    return mocker.patch("src.services.auth_service.bcrypt")


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.services.auth_service.jwt")


def test_logout_user(app, mock_db):
    with app.app_context():
        mock_db.revoked_tokens.insert_one.return_value.inserted_id = "inserted_id_example"
        validate_success_response_generic(revoke_access_token(VALID_JWT), 201)


def test_check_if_token_revoked(mock_db):
    jwt_payload = {"jti": VALID_JWT["jti"]}
    jwt_header = {"alg": "HS256", "typ": "JWT"}
    mock_db.revoked_tokens.find_one.return_value = VALID_JWT
    token_revoked = check_if_token_revoked(jwt_header, jwt_payload)
    assert token_revoked is True


def test_revoked_token_callback(app, mock_db):
    with app.app_context():
        validate_error_response_specific(revoked_token_callback(None, None), 401, "El token ha sido revocado")


def test_expired_token_callback(app):
    with app.app_context():
        validate_error_response_specific(expired_token_callback(None, None), 401, "El token ha expirado")


def test_unauthorized_callback(app):
    with app.app_context():
        response, status_code = unauthorized_callback("error_message")
        assert status_code == 401
        assert response.json == {"err": "Necesita un token válido para acceder a esta ruta"}
