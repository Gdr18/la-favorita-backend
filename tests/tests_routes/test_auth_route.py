import pytest
from pymongo.errors import PyMongoError
from flask_jwt_extended import create_access_token, create_refresh_token
from flask import Response

from src.app import run_app
from config import config
from src.models.user_model import UserModel
from src.models.token_model import TokenModel


VALID_LOGIN_DATA = {"_id": "507f1f77bcf86cd799439011", "name": "TestUser", "email": "test_user@outlook.com", "password": "_Test1234", "confirmed": True, "auth_provider": "email"}
INVALID_LOGIN_DATA = {"_id": "507f1f77bcf86cd799439011", "name": "TestUser", "email": "test_user@outlook.com", "password": "wrong_password", "confirmed": True}


@pytest.fixture
def app():
    app = run_app(config)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_header(app):
    with app.app_context():
        access_token = create_access_token(identity="507f1f77bcf86cd799439011", additional_claims={"role": 1}, fresh=True)
        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_header_refresh(app):
    with app.app_context():
        refresh_token = create_refresh_token(identity="507f1f77bcf86cd799439011", additional_claims={"role": 1})
        return {"Authorization": f"Bearer {refresh_token}"}


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.routes.auth_route.get_jwt")


def test_register_success(mocker, client):
    mock_insert_result = mocker.MagicMock()
    mock_insert_result.inserted_id = VALID_LOGIN_DATA["_id"]
    mocker.patch.object(UserModel, "insert_user", return_value=mock_insert_result)
    mocker.patch("src.routes.auth_route.send_email")

    response = client.post(
        "/auth/register",
        json={"password": VALID_LOGIN_DATA["password"], "name": "Test User", "email": VALID_LOGIN_DATA["email"]},
    )

    assert response.status_code == 201
    assert response.json["msg"] == "Usuario '507f1f77bcf86cd799439011' ha sido añadido de forma satisfactoria"


def test_register_with_role_error(client):
    response = client.post(
        "/auth/register",
        json={**INVALID_LOGIN_DATA, "role": 3},
    )

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a establecer 'role'"


def test_register_database_error(mocker, client):
    mock_user = mocker.MagicMock()
    mock_user.insert_user.side_effect = PyMongoError("Database error")
    mocker.patch("src.routes.auth_route.UserModel", return_value=mock_user)

    response = client.post(
        "/auth/register",
        json=INVALID_LOGIN_DATA,
    )

    assert response.status_code == 500
    assert response.json["err"] == "Ha ocurrido un error en MongoDB: Database error"


def test_change_email_auth_provider_email_success(client, auth_header, mock_jwt, mocker):
    mock_jwt.return_value = {"role": 3, "sub": VALID_LOGIN_DATA["_id"]}
    mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value={"email": VALID_LOGIN_DATA["email"], "password": VALID_LOGIN_DATA["password"], "name": "TestUser", "auth_provider": "email", "confirmed": True})
    mocker.patch.object(UserModel, "update_user", return_value={"email": "testuser2@outlook.com", "password": VALID_LOGIN_DATA["password"], "name": "TestUser", "auth_provider": "email", "confirmed": True})
    mocker.patch("src.routes.auth_route.send_email")

    response = client.post("/auth/change-email", json={"password": VALID_LOGIN_DATA["password"], "email": "testuser2@outlook.com"}, headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == "Email del usuario '507f1f77bcf86cd799439011' ha sido cambiado de forma satisfactoria"


def test_change_email_auth_provider_google_success(client, auth_header, mock_jwt, mocker):
    mock_jwt.return_value = {"role": 3, "sub": VALID_LOGIN_DATA["_id"]}
    mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value={"email": "testuser@google.com", "name": "TestUser", "auth_provider": "google", "confirmed": True})
    mocker.patch.object(UserModel, "update_user", return_value={"email": "testuser2@outlook.com", "name": "TestUser", "password": VALID_LOGIN_DATA["password"], "auth_provider": "email", "confirmed": False})
    mocker.patch("src.routes.auth_route.send_email")

    response = client.post("/auth/change-email", json={"email": "testuser2@outlook.com", "password": VALID_LOGIN_DATA["password"]}, headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == "Email del usuario '507f1f77bcf86cd799439011' ha sido cambiado de forma satisfactoria"


def test_change_email_without_password(client, auth_header, mock_jwt, mocker):
    mock_jwt.return_value({"role": 3, "sub": VALID_LOGIN_DATA["_id"]})
    mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value={"email": VALID_LOGIN_DATA["email"], "name": "TestUser", "auth_provider": "google"})

    response = client.post("/auth/change-email", json={"email": "testuser2@outlook.com"}, headers=auth_header)

    assert response.status_code == 500
    assert response.json["err"] == "Ha ocurrido un error inesperado. Se necesita contraseña para cambiar el email"


def test_login_success(client, mocker):
    mocker.patch.object(UserModel, "get_user_by_email", return_value={**VALID_LOGIN_DATA, "password": "$2b$12$KIXIDFj8Nf8eVwX1WcQO2u5F9J1z1F9J1z1F9J1z1F9J1z1F9J1z1F9"})

    mocker.patch("src.routes.auth_route.verify_password", return_value=True)
    mocker.patch("src.routes.auth_route.generate_access_token", return_value="access_token")
    mocker.patch("src.routes.auth_route.generate_refresh_token", return_value="refresh_token")

    response = client.post("/auth/login", json=VALID_LOGIN_DATA)

    assert response.status_code == 200
    assert response.json["msg"] == f"El usuario '{VALID_LOGIN_DATA['_id']}' ha iniciado sesión de forma manual"
    assert response.json["access_token"] == "access_token"
    assert response.json["refresh_token"] == "refresh_token"


def test_login_user_not_found(client, mocker):
    mocker.patch.object(UserModel, "get_user_by_email", return_value=None)

    response = client.post("/auth/login", json=VALID_LOGIN_DATA)

    assert response.status_code == 404
    assert response.json["err"] == "Usuario no encontrado"


def test_login_password_not_match(client, mocker):
    mocker.patch.object(UserModel, "get_user_by_email", return_value=INVALID_LOGIN_DATA)
    mocker.patch("src.routes.auth_route.verify_password", return_value=False)

    response = client.post("/auth/login", json=INVALID_LOGIN_DATA)

    assert response.status_code == 401
    assert response.json["err"] == "La contraseña no coincide"


def test_login_user_not_confirmed(client, mocker):
    mocker.patch.object(UserModel, "get_user_by_email", return_value={**INVALID_LOGIN_DATA, "confirmed": False})
    mocker.patch("src.routes.auth_route.verify_password", return_value=True)

    response = client.post("/auth/login", json=INVALID_LOGIN_DATA)

    assert response.status_code == 401
    assert response.json["err"] == "El email no está confirmado"


def test_logout_success(client, auth_header, mock_jwt, mocker):
    mock_jwt.return_value = {"role": 3, "sub": VALID_LOGIN_DATA["_id"]}
    mocker.patch("src.routes.auth_route.revoke_access_token")
    mocker.patch("src.routes.auth_route.delete_refresh_token")

    response = client.post("/auth/logout", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Logout del usuario '{VALID_LOGIN_DATA['_id']}' ha sido realizado de forma satisfactoria"


def test_login_google_success(client, mocker):
    mocker.patch("src.routes.auth_route.google.authorize_redirect", side_effect=lambda uri: Response(
        status=302,
        headers={"Location": uri}
    ))

    response = client.get("/auth/login/google")

    assert response.status_code == 302
    assert response.headers["Location"] == "http://localhost/auth/callback/google"


def test_callback_google_success(client, mocker):
    mocker.patch("src.routes.auth_route.google.authorize_access_token")
    mocker.patch("src.routes.auth_route.google.parse_id_token", return_value={"name": "test_user", "email": "test_user@google.com"})
    mocker.patch.object(UserModel, "insert_or_update_user_by_email", return_value=VALID_LOGIN_DATA)

    mocker.patch("src.routes.auth_route.generate_access_token", return_value="access_token")
    mocker.patch("src.routes.auth_route.generate_refresh_token", return_value="refresh_token")

    response = client.get("/auth/callback/google")

    assert response.status_code == 200
    assert response.json["msg"] == "El usuario '507f1f77bcf86cd799439011' ha iniciado sesión con Google"
    assert response.json["access_token"] == "access_token"
    assert response.json["refresh_token"] == "refresh_token"


def test_refresh_token_success(client, auth_header_refresh, mock_jwt, mocker):
    mock_jwt.return_value({"role": 3, "sub": VALID_LOGIN_DATA["_id"]})
    mocker.patch.object(TokenModel, "get_refresh_token_by_user_id", return_value={
        "user_id": VALID_LOGIN_DATA["_id"],
        "jti": "123e4567-e89b-12d3-a456-426614174000",
        "created_at": "2025-10-10T12:00:00Z",
        "expires_at": "2025-12-10T12:00:00Z"
    })
    mocker.patch.object(UserModel, "get_user_by_user_id", return_value=VALID_LOGIN_DATA)
    mocker.patch("src.routes.auth_route.generate_access_token", return_value="new_access_token")

    response = client.get("/auth/refresh-token", headers=auth_header_refresh)

    assert response.status_code == 200
    assert response.json["msg"] == "El token de acceso se ha generado"
    assert response.json["access_token"] == "new_access_token"


def test_refresh_token_error(client, auth_header_refresh, mock_jwt, mocker):
    mock_jwt.return_value({"role": 3, "sub": VALID_LOGIN_DATA["_id"]})
    mocker.patch.object(TokenModel, "get_refresh_token_by_user_id", return_value=None)

    response = client.get("/auth/refresh-token", headers=auth_header_refresh)

    assert response.status_code == 404
    assert response.json["err"] == "Refresh token no encontrado"


def test_confirm_email_success(client, mocker):
    mocker.patch("src.routes.auth_route.decode_token", return_value={"sub": VALID_LOGIN_DATA["_id"]})
    mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value={"name": "TestUser", "email": VALID_LOGIN_DATA["email"], "password": VALID_LOGIN_DATA["password"], "auth_provider": "email", "confirmed": False})
    mocker.patch.object(UserModel, "update_user", return_value={**VALID_LOGIN_DATA, "confirmed": True})

    response = client.get("/auth/confirm-email/test_token")

    assert response.status_code == 200
    assert response.json["msg"] == f"""Usuario '{VALID_LOGIN_DATA["_id"]}' ha sido confirmado de forma satisfactoria"""


def test_confirm_email_user_not_found(client, mocker):
    mocker.patch("src.routes.auth_route.decode_token", return_value={"sub": VALID_LOGIN_DATA["_id"]})
    mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value=None)

    response = client.get("/auth/confirm-email/test_token")

    assert response.status_code == 404
    assert response.json["err"] == "Usuario no encontrado"


def test_confirm_email_invalid_token(client, mocker):
    mocker.patch("src.routes.auth_route.decode_token", side_effect=Exception("Invalid token"))

    response = client.get("/auth/confirm-email/test_token")

    assert response.status_code == 500
    assert response.json["err"] == "Ha ocurrido un error inesperado. Invalid token"


def test_resend_email_success(client, mocker):
    mocker.patch.object(TokenModel, "get_email_tokens_by_user_id", return_value=[{"user_id": VALID_LOGIN_DATA["_id"], "jti": "123e4567-e89b-12d3-a456-426614174000", "created_at": "2025-10-10T12:00:00Z", "expires_at": "2025-12-10T12:00:00Z"}])
    mocker.patch.object(UserModel, "get_user_by_user_id", return_value=VALID_LOGIN_DATA)
    mocker.patch("src.routes.auth_route.send_email")

    response = client.post("/auth/resend-email/507f1f77bcf86cd799439011")

    assert response.status_code == 200
    assert response.json["msg"] == f"""Email de confirmación del usuario '507f1f77bcf86cd799439011' ha sido reenviado de forma satisfactoria"""


def test_resend_email_user_not_found(client, mocker):
    mocker.patch.object(TokenModel, "get_email_tokens_by_user_id", return_value=[{"user_id": VALID_LOGIN_DATA["_id"], "jti": "123e4567-e89b-12d3-a456-426614174000", "created_at": "2025-10-10T12:00:00Z", "expires_at": "2025-12-10T12:00:00Z"}])
    mocker.patch.object(UserModel, "get_user_by_user_id", return_value=None)

    response = client.post("/auth/resend-email/507f1f77bcf86cd799439011")

    assert response.status_code == 404
    assert response.json["err"] == "Usuario no encontrado"


def test_resend_email_too_many_requests(client, mocker):
    mocker.patch.object(TokenModel, "get_email_tokens_by_user_id", return_value=[{"user_id": VALID_LOGIN_DATA["_id"], "jti": "123e4567-e89b-12d3-a456-426614174000", "created_at": "2025-10-10T12:00:00Z", "expires_at": "2025-12-10T12:00:00Z"}] * 5)

    response = client.post("/auth/resend-email/507f1f77bcf86cd799439011")

    assert response.status_code == 429
    assert response.json["err"] == "Se han reenviado demasiados emails de confirmación. Inténtalo mañana."

