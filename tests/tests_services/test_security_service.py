import pytest
import re

from config import config
from src.app import run_app
from src.services.security_service import (
    google,
    verify_password,
    verify_google_identity,
    generate_access_token,
    generate_refresh_token,
    generate_email_token,
    revoke_access_token,
    delete_refresh_token,
    check_if_token_revoked,
    revoked_token_callback,
    expired_token_callback,
    unauthorized_callback,
)
from tests.tests_utils.test_exceptions_management import validate_error_response_specific

JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
VALID_JWT = {"jti": "bb53e637-8627-457c-840f-6cae52a12e8b", "exp": 1919068218}
VALID_USER_DATA = {
    "_id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john.doe@outlook.com",
    "password": "ValidPass123!",
    "role": 1,
    "phone": "+34666666666",
    "basket": [{"name": "galletas", "qty": 1, "price": 3.33}],
    "addresses": [{"line_one": "Calle Falsa 123", "postal_code": "12345"}],
}
JWT_PATTERN = re.compile(r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+$")


@pytest.fixture
def app():
    app = run_app(config)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def mock_db_revoked_tokens(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.revoked_tokens", new=mock_db)
    return mock_db


@pytest.fixture
def mock_db_email_tokens(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.email_tokens", new=mock_db)
    return mock_db


@pytest.fixture
def mock_db_refresh_tokens(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.refresh_tokens", new=mock_db)
    return mock_db


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.services.security_service.jwt")


def test_verify_password(mocker):
    mocker.patch("src.services.security_service.bcrypt.check_password_hash", return_value=True)
    db_password = "hashed_password"
    password = "plain_password"
    result = verify_password(db_password, password)
    assert result is True


def test_verify_google_identity(mocker, app):
    google_token = "fake_google_token"
    user_email = "user@example.com"
    with app.app_context():
        mock_parse_id_token = mocker.patch.object(google, "parse_id_token")
        mock_parse_id_token.return_value = {"email": user_email}
        result = verify_google_identity(google_token, user_email)
        assert result is True


def test_generate_access_token(mock_jwt, app):
    with app.app_context():
        mock_jwt.create_access_token.return_value = JWT
        result = generate_access_token(VALID_USER_DATA)
        assert JWT_PATTERN.match(result)


def test_generate_refresh_token(mock_jwt, mock_db_refresh_tokens, app):
    with app.app_context():
        mock_jwt.generate_refresh_token.return_value = JWT
        mock_db_refresh_tokens.insert_one.return_value = {"inserted_id": "507f1f77bcf86cd799439011"}
        result = generate_refresh_token(VALID_USER_DATA)
        assert JWT_PATTERN.match(result)
        assert mock_db_refresh_tokens.insert_one.called


def test_check_if_token_revoked(mock_db_revoked_tokens):
    jwt_payload = {"jti": VALID_JWT["jti"]}
    mock_db_revoked_tokens.revoked_tokens.find_one.return_value = VALID_JWT
    token_revoked = check_if_token_revoked(None, jwt_payload)
    assert token_revoked is True


def test_revoked_token_callback(app):
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
