import pytest
import json

from tests.test_helpers import app, client, auth_header
from src.models.token_model import TokenModel


ID = "507f1f77bcf86cd799439011"
VALID_REVOKED_TOKEN_DATA = {
    "user_id": ID,
    "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
    "expires_at": "2025-10-01T00:00:00Z",
}


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.routes.revoked_tokens_route.get_jwt")


@pytest.mark.parametrize("url, method", [
    ("/revoked-tokens/", "post"),
    ("/revoked-tokens/", "get"),
    ("/revoked-tokens/507f1f77bcf86cd799439011", "delete"),
    ("/revoked-tokens/507f1f77bcf86cd799439011", "put"),
    ("/revoked-tokens/507f1f77bcf86cd799439011", "get"),
])
def test_token_not_authorized_error(mock_jwt, client, auth_header, url, method):
    mock_jwt.return_value = {"role": 1}

    if method == "post":
        response = client.post(url, json=VALID_REVOKED_TOKEN_DATA, headers=auth_header)
    elif method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_REVOKED_TOKEN_DATA, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


@pytest.mark.parametrize("url, method", [
    ("/revoked-tokens/507f1f77bcf86cd799439011", "get"),
    ("/revoked-tokens/507f1f77bcf86cd799439011", "delete"),
    ("/revoked-tokens/507f1f77bcf86cd799439011", "put"),
])
def test_revoked_token_not_found_error(mocker, client, auth_header, mock_jwt, url, method):
    mock_jwt.return_value = {"role": 0}

    if method in ["get", "put"]:
        mocker.patch.object(TokenModel, "get_revoked_token_by_token_id", return_value=None)
    else:
        mocker.patch.object(TokenModel, "delete_revoked_token", return_value=mocker.MagicMock(deleted_count=0))

    if method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_REVOKED_TOKEN_DATA, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Token revocado no encontrado"


def test_add_revoked_token_success(mocker, client, mock_jwt, auth_header):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(
        TokenModel,
        "insert_revoked_token",
        return_value=mocker.MagicMock(inserted_id=ID),
    )

    response = client.post(
        "/revoked-tokens/", json=VALID_REVOKED_TOKEN_DATA, headers=auth_header
    )

    assert response.status_code == 201
    assert response.json["msg"] == f"Token revocado '{ID}' ha sido añadido de forma satisfactoria"


def test_get_revoked_tokens_success(mocker, mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "get_revoked_tokens", return_value=[VALID_REVOKED_TOKEN_DATA])

    response = client.get("/revoked-tokens/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_REVOKED_TOKEN_DATA]


def test_get_revoked_token_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "get_revoked_token_by_token_id", return_value=VALID_REVOKED_TOKEN_DATA)

    response = client.get(f"/revoked-tokens/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_REVOKED_TOKEN_DATA


def test_update_revoked_token_success(mocker, mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "get_revoked_token_by_token_id", return_value=VALID_REVOKED_TOKEN_DATA)
    mocker.patch.object(TokenModel, "update_revoked_token", return_value={**VALID_REVOKED_TOKEN_DATA, "expires_at": "2025-10-01T00:00:00Z"})

    response = client.put(f"/revoked-tokens/{ID}", json={"expires_at": "2025-10-01T00:00:00Z"}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_REVOKED_TOKEN_DATA, "expires_at": "2025-10-01T00:00:00Z"}


def test_delete_revoked_token_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "delete_revoked_token", return_value=mocker.MagicMock(deleted_count=1))

    response = client.delete(f"/revoked-tokens/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Token revocado '{ID}' ha sido eliminado de forma satisfactoria"
