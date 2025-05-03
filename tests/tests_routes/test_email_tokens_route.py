import pytest
import json

from src.models.token_model import TokenModel
from tests.test_helpers import app, client, auth_header


VALID_EMAIL_TOKEN_DATA = {"user_id": "507f1f77bcf86cd799439011", "jti": "123e4567-e89b-42d3-a456-426614174000", "expires_at": "2025-10-01T00:00:00Z"}
ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.routes.email_tokens_route.get_jwt")


def test_add_email_token_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "insert_email_token", return_value=mocker.MagicMock(inserted_id=ID))

    response = client.post("/email-tokens/", json=VALID_EMAIL_TOKEN_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Email token '{ID}' ha sido añadido de forma satisfactoria"


def test_add_email_token_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 1}

    response = client.post("/email-tokens/", json=VALID_EMAIL_TOKEN_DATA, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_get_email_tokens_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "get_email_tokens", return_value=[VALID_EMAIL_TOKEN_DATA])

    response = client.get("/email-tokens/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_EMAIL_TOKEN_DATA]


def test_get_email_tokens_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 1}

    response = client.get("/email-tokens/", headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_handle_email_token_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 1}

    response = client.get(f"/email-tokens/{ID}", headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_get_email_token_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "get_email_token_by_token_id", return_value=VALID_EMAIL_TOKEN_DATA)

    response = client.get(f"/email-tokens/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_EMAIL_TOKEN_DATA


def test_get_email_token_not_found(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "get_email_token_by_token_id", return_value=None)

    response = client.get(f"/email-tokens/{ID}", headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Email token no encontrado"


def test_update_email_token_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "get_email_token_by_token_id", return_value=VALID_EMAIL_TOKEN_DATA)
    mocker.patch.object(TokenModel, "update_email_token", return_value={**VALID_EMAIL_TOKEN_DATA, "expires_at": "2025-10-02T00:00:00Z"})

    response = client.put(f"/email-tokens/{ID}", json={**VALID_EMAIL_TOKEN_DATA, "expires_at": "2025-10-02T00:00:00Z"}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_EMAIL_TOKEN_DATA, "expires_at": "2025-10-02T00:00:00Z"}


def test_update_email_token_not_found(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "get_email_token_by_token_id", return_value=None)

    response = client.put(f"/email-tokens/{ID}", json={**VALID_EMAIL_TOKEN_DATA, "expires_at": "2025-10-02T00:00:00Z"}, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Email token no encontrado"


def test_delete_email_token_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "delete_email_token", return_value=mocker.MagicMock(deleted_count=1))

    response = client.delete(f"/email-tokens/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Email token '{ID}' ha sido eliminado de forma satisfactoria"


def test_delete_email_token_not_found(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(TokenModel, "delete_email_token", return_value=mocker.MagicMock(deleted_count=0))

    response = client.delete(f"/email-tokens/{ID}", headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Email token no encontrado"
