import pytest
import json

from src.models.setting_model import SettingModel
from tests.test_helpers import app, client, auth_header

ID = "507f1f77bcf86cd799439011"
VALID_SETTING_DATA = {"name": "test", "values": ["value1", "value2"]}


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.routes.settings_route.get_jwt")


@pytest.mark.parametrize("url, method", [
    ("/settings/", "post"),
    ("/settings/", "get"),
    ("/settings/507f1f77bcf86cd799439011", "delete"),
    ("/settings/507f1f77bcf86cd799439011", "put"),
    ("/settings/507f1f77bcf86cd799439011", "get"),
])
def test_not_authorized_token_error(mock_jwt, client, auth_header, url, method):
    mock_jwt.return_value = {"role": 3}

    if method == "post":
        response = client.post(url, json=VALID_SETTING_DATA, headers=auth_header)
    elif method == "get" or method == "delete":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_SETTING_DATA, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


@pytest.mark.parametrize("url, method", [
    ("/settings/507f1f77bcf86cd799439011", "get"),
    ("/settings/507f1f77bcf86cd799439011", "delete"),
    ("/settings/507f1f77bcf86cd799439011", "put"),
])
def test_not_found_error(mocker, mock_jwt, client, auth_header, url, method):
    mock_jwt.return_value = {"role": 1}

    if method in ["get", "put"]:
        mocker.patch.object(SettingModel, "get_setting", return_value=None)
    else:
        mocker.patch.object(SettingModel, "delete_setting", return_value=mocker.MagicMock(deleted_count=0))

    if method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_SETTING_DATA, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Configuración no encontrado"


def test_add_setting_success(mock_jwt, mocker, client, auth_header):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(
        SettingModel,
        "insert_setting",
        return_value=mocker.MagicMock(inserted_id=ID),
    )

    response = client.post("/settings/", json=VALID_SETTING_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Configuración '{ID}' ha sido añadida de forma satisfactoria"


def test_get_settings_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 0}
    mocker.patch.object(SettingModel, "get_settings", return_value=[VALID_SETTING_DATA])

    response = client.get("/settings/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_SETTING_DATA]


def test_get_setting_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(SettingModel, "get_setting", return_value=VALID_SETTING_DATA)

    response = client.get(f"/settings/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_SETTING_DATA


def test_update_setting_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(SettingModel, "get_setting", return_value=VALID_SETTING_DATA)
    mocker.patch.object(SettingModel, "update_setting", return_value={**VALID_SETTING_DATA, "name": "new_value"})

    response = client.put(f"/settings/{ID}", json={"name": "new_value"}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_SETTING_DATA, "name": "new_value"}


def test_delete_setting_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(SettingModel, "delete_setting", return_value=mocker.MagicMock(deleted_count=1))

    response = client.delete(f"/settings/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Configuración '{ID}' ha sido eliminada de forma satisfactoria"

