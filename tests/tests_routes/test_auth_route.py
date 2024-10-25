import pytest
from flask_jwt_extended import create_access_token
from pymongo.errors import DuplicateKeyError

from src import app as real_app
from src.utils.exceptions_management import ClientCustomError


VALID_LOGIN_DATA = {"username": "test_user", "password": "_Test1234"}
INVALID_LOGIN_DATA = {"username": "test_user", "password": "wrong_password"}

URL_LOGIN = "/login"
URL_LOGOUT = "/logout"


@pytest.fixture
def app():
    real_app.config["TESTING"] = True
    yield real_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def authorized_header(app):
    with app.app_context():
        access_token = create_access_token(identity="test_user", fresh=True, additional_claims={"role": 1})
        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_login_user_function(mocker):
    return mocker.patch("src.routes.auth_route.login_user")


@pytest.fixture
def mock_logout_user_function(mocker):
    return mocker.patch("src.routes.auth_route.logout_user")


def test_login_successful(client, mock_login_user_function):
    mock_login_user_function.return_value = ({"msg": "Token '234' ha sido creado de forma satisfactoria"}, 200)
    response = client.post(URL_LOGIN, json=VALID_LOGIN_DATA)
    assert response.status_code == 200
    assert "msg" in response.json


def test_login_user_not_found(client, mock_login_user_function):
    mock_login_user_function.side_effect = ClientCustomError("usuario", "not_found")
    response = client.post(URL_LOGIN, json=INVALID_LOGIN_DATA)
    assert response.status_code == 404
    assert "err" in response.json


def test_login_password_not_match(client, mock_login_user_function):
    mock_login_user_function.side_effect = ClientCustomError("password", "not_match")
    response = client.post(URL_LOGIN, json=INVALID_LOGIN_DATA)
    assert response.status_code == 401
    assert "err" in response.json


def test_login_unexpected_error(client, mock_login_user_function):
    mock_login_user_function.side_effect = Exception("Unexpected error")
    response = client.post(URL_LOGIN, json=VALID_LOGIN_DATA)
    assert response.status_code == 500
    assert "err" in response.json


def test_logout_successful(client, mock_logout_user_function, authorized_header):
    mock_logout_user_function.return_value = ({"msg": "Token revocado '2345' ha sido añadido de forma satisfactoria"}, 200)
    response = client.post(URL_LOGOUT, headers=authorized_header)
    assert response.status_code == 200
    assert "msg" in response.json


def test_logout_duplicate_key_error(client, mock_logout_user_function, authorized_header, mocker):
    mock_logout_user_function.side_effect = DuplicateKeyError("E11000 duplicate key error")
    mocker.patch('pymongo.errors.DuplicateKeyError.details', new_callable=mocker.PropertyMock, return_value={"keyValue": {"jti": "test_jti"}})
    response = client.post(URL_LOGOUT, headers=authorized_header)
    assert response.status_code == 409
    assert "err" in response.json


def test_logout_unexpected_error(client, mock_logout_user_function, authorized_header):
    mock_logout_user_function.side_effect = Exception("Unexpected error")
    response = client.post(URL_LOGOUT, headers=authorized_header)
    assert response.status_code == 500
    assert "err" in response.json
