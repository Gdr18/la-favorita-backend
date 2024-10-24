import pytest

from src import app as real_app
from src.services.auth_service import login_user, logout_user, check_if_token_revoked, revoked_token_callback, expired_token_callback, unauthorized_callback
from src.utils.exceptions_management import ClientCustomError

VALID_JWT = {
    "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
    "exp": 1919068218
}


@pytest.fixture
def app():
    real_app.config['TESTING'] = True
    return real_app


@pytest.fixture
def mock_db(mocker):
    return mocker.patch('src.services.auth_service.db')


@pytest.fixture
def mock_bcrypt(mocker):
    return mocker.patch('src.services.auth_service.bcrypt')


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch('src.services.auth_service.jwt')


def test_login_user_success(app, mock_db, mock_bcrypt, mock_jwt):
    with app.app_context():
        user_data = {"email": "test@example.com", "password": "_Password123"}
        user_request = {"_id": "user_id", "password": "hashed_password", "role": 2}
        mock_db.users.find_one.return_value = user_request
        mock_bcrypt.check_password_hash.return_value = True
        response, status_code = login_user(user_data)

        assert status_code == 200
        assert "msg" in response.json


def test_login_user_invalid_password(mock_db, mock_bcrypt):
    user_data = {"email": "test@example.com", "password": "wrong_password"}
    user_request = {"_id": "user_id", "password": "hashed_password", "role": "user"}
    mock_db.users.find_one.return_value = user_request
    mock_bcrypt.check_password_hash.return_value = False

    with pytest.raises(ClientCustomError):
        login_user(user_data)


def test_login_user_email_not_found(mock_db):
    user_data = {"email": "test@example.com", "password": "_Password123"}
    mock_db.users.find_one.return_value = None
    with pytest.raises(ClientCustomError):
        login_user(user_data)


def test_logout_user(app, mock_db):
    with app.app_context():
        mock_db.revoked_tokens.insert_one.return_value.inserted_id = "inserted_id_example"
        response, status_code = logout_user(VALID_JWT["jti"], VALID_JWT["exp"])

        assert status_code == 201
        assert "inserted_id_example" in response.json["msg"]


def test_check_if_token_revoked(mock_db):
    jwt_payload = {"jti": VALID_JWT["jti"]}
    mock_db.revoked_tokens.find_one.return_value = VALID_JWT
    token_revoked = check_if_token_revoked(None, jwt_payload)
    assert token_revoked is True


def test_revoked_token_callback(app, mock_db):
    with app.app_context():
        response, status_code = revoked_token_callback(None, None)

        assert status_code == 401
        assert response.json["err"] == "El token ha sido revocado"


def test_expired_token_callback(app):
    with app.app_context():
        response, status_code = expired_token_callback(None, None)

        assert status_code == 401
        assert response.json["err"] == "El token ha expirado"


def test_unauthorized_callback(app):
    with app.app_context():
        response, status_code = unauthorized_callback("error_message")

        assert status_code == 401
        assert response.json["err"] == "Necesita un token autorizado para acceder a esta ruta"
