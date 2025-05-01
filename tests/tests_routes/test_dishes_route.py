import pytest
import json

from src.models.dish_model import DishModel
from tests.tests_tools import app, client, auth_header


VALID_DISH_DATA = {"name": "Pizza", "description": "Delicious pizza", "category": "main", "ingredients": [{"name": "tomato", "waste": 0}], "price": 10.99, "available": True}
ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.routes.dishes_route.get_jwt")


def test_insert_dish_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(DishModel, "insert_dish", return_value=mocker.MagicMock(inserted_id=ID))

    response = client.post("/dishes/", json=VALID_DISH_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Plato '{ID}' ha sido añadido de forma satisfactoria"


def test_insert_dish_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 2}

    response = client.post("/dishes/", json=VALID_DISH_DATA, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_get_dishes_success(mocker, client):
    mocker.patch.object(DishModel, "get_dishes", return_value=[VALID_DISH_DATA])

    response = client.get("/dishes/")

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_DISH_DATA]


def test_get_dishes_by_category_success(mocker, client):
    mocker.patch.object(DishModel, "get_dishes_by_category", return_value=[VALID_DISH_DATA])

    response = client.get("/dishes/category/main")

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_DISH_DATA]


def test_get_dish_success(mocker, client):
    mocker.patch.object(DishModel, "get_dish", return_value=VALID_DISH_DATA)

    response = client.get(f"/dishes/{ID}")

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_DISH_DATA


def test_get_dish_not_found(mocker, client):
    mocker.patch.object(DishModel, "get_dish", return_value=None)

    response = client.get(f"/dishes/{ID}")

    assert response.status_code == 404
    assert response.json["err"] == "Plato no encontrado"


def test_handle_dish_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 2}

    response = client.put(f"/dishes/{ID}", json=VALID_DISH_DATA, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_update_dish_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(DishModel, "get_dish", return_value=VALID_DISH_DATA)
    mocker.patch.object(DishModel, "update_dish", return_value={**VALID_DISH_DATA, "name": "Updated Pizza"})

    response = client.put(f"/dishes/{ID}", json={**VALID_DISH_DATA, "name": "Updated Pizza"}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_DISH_DATA, "name": "Updated Pizza"}


def test_update_dish_not_found(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(DishModel, "get_dish", return_value=None)

    response = client.put(f"/dishes/{ID}", json=VALID_DISH_DATA, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Plato no encontrado"


def test_delete_dish_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(DishModel, "delete_dish", return_value=mocker.MagicMock(deleted_count=1))

    response = client.delete(f"/dishes/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Plato '{ID}' ha sido eliminado de forma satisfactoria"


def test_delete_dish_not_found(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(DishModel, "delete_dish", return_value=mocker.MagicMock(deleted_count=0))

    response = client.delete(f"/dishes/{ID}", headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Plato no encontrado"
