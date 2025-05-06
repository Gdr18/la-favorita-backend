import pytest
import json

from src.models.user_model import UserModel
from tests.test_helpers import app, client, auth_header

VALID_USER_DATA = {
    "name": "John Doe",
    "email": "john.doe@hotmail.com",
    "password": "ValidPass123!",
}
ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.routes.users_route.get_jwt")


@pytest.mark.parametrize("url, method", [
    ("/users/", "post"),
    ("/users/", "get"),
    ("/users/507f1f77bcf86cd799439012", "get"),
    ("/users/507f1f77bcf86cd799439012", "delete"),
    ("/users/507f1f77bcf86cd799439012", "put"),
])
def test_not_authorized_token_error(mock_jwt, client, auth_header, url, method):
    mock_jwt.return_value = {"role": 3, "sub": ID}

    if method == "post":
        response = client.post(url, json=VALID_USER_DATA, headers=auth_header)
    elif method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_USER_DATA, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


@pytest.mark.parametrize("url, method", [
    ("/users/507f1f77bcf86cd799439011", "get"),
    ("/users/507f1f77bcf86cd799439011", "delete"),
    ("/users/507f1f77bcf86cd799439011", "put"),
])
def test_not_found_error(mocker, mock_jwt, client, auth_header, url, method):
    mock_jwt.return_value = {"role": 0, "sub": ID}

    if method in ["get", "put"]:
        mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value=None)
    else:
        mocker.patch.object(UserModel, "delete_user", return_value=mocker.MagicMock(deleted_count=0))

    if method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_USER_DATA, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == f"Usuario no encontrado"


@pytest.mark.parametrize("field", [{"email": "invalid_email"}, {"role": 2}])
def test_not_authorized_to_set_error(mocker, client, auth_header, field):
    mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value=VALID_USER_DATA)

    response = client.put(f"/users/{ID}", json=field, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == f"El token no está autorizado a establecer '{list(field.keys())[0]}'"


def test_add_user_success(mocker, client, mock_jwt, auth_header):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(
        UserModel, "insert_user", return_value=mocker.MagicMock(inserted_id=ID)
    )

    response = client.post("/users/", json=VALID_USER_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Usuario '{ID}' ha sido añadido de forma satisfactoria"


def test_get_users_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(UserModel, "get_users", return_value=[VALID_USER_DATA])

    response = client.get("/users/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_USER_DATA]


def test_get_user_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0, "sub": ID}
    mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value=VALID_USER_DATA)

    response = client.get(f"/users/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_USER_DATA


def test_update_user_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0, "sub": ID, "jti": "bb53e637-8627-457c-840f-6cae52a12e8b"}
    mocker.patch.object(UserModel, "get_user_by_user_id_without_id", return_value=VALID_USER_DATA)
    mocker.patch.object(UserModel, "update_user", return_value={**VALID_USER_DATA, "name": "Updated User"})

    response = client.put(f"/users/{ID}", json={"name": "Updated User"}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_USER_DATA, "name": "Updated User"}


def test_delete_user_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0, "sub": ID}
    mocker.patch.object(UserModel, "delete_user", return_value=mocker.MagicMock(deleted_count=1))
    mocker.patch("src.routes.users_route.revoke_access_token")
    mocker.patch("src.routes.users_route.delete_refresh_token")

    response = client.delete(f"/users/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Usuario '{ID}' ha sido eliminado de forma satisfactoria"
