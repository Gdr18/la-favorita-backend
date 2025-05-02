import pytest
import json
from pymongo.errors import PyMongoError

from tests.test_helpers import app, client, auth_header
from src.models.product_model import ProductModel
from src.models.dish_model import DishModel


VALID_PRODUCT_DATA = {
    "name": "Cacahuetes",
    "stock": 345,
    "categories": ["snack", "otro"],
    "allergens": ["cacahuete"],
    "brand": "marca",
    "notes": "notas",
}
INVALID_PRODUCT_DATA = {"name": 12345, "stock": 345, "categories": ["snack", "otro"]}
UPDATED_PRODUCT_DATA = {"name": "new_value"}
ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def mock_jwt(mocker):
    return mocker.patch("src.routes.products_route.get_jwt")


def test_add_product_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(
        ProductModel,
        "insert_product",
        return_value=mocker.MagicMock(inserted_id=ID),
    )

    response = client.post("/products/", json=VALID_PRODUCT_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Producto '{ID}' ha sido añadido de forma satisfactoria"


def test_add_product_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 3}

    response = client.post("/products/", json=VALID_PRODUCT_DATA, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_get_products_success(mocker, mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(ProductModel, "get_products", return_value=[VALID_PRODUCT_DATA])

    response = client.get("/products/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_PRODUCT_DATA]


def test_get_products_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 3}

    response = client.get("/products/", headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_update_product_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(ProductModel, "get_product", return_value=VALID_PRODUCT_DATA)
    mocker.patch.object(
        ProductModel,
        "update_product",
        return_value={**VALID_PRODUCT_DATA, **UPDATED_PRODUCT_DATA, "stock": 0},
    )
    mocker.patch.object(
        DishModel,
        "update_dishes_availability",
        return_value=mocker.MagicMock(updated_id=ID),
    )

    response = client.put(
        f"/products/{ID}", json={**UPDATED_PRODUCT_DATA, "stock": 0}, headers=auth_header
    )

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_PRODUCT_DATA, **UPDATED_PRODUCT_DATA, "stock": 0}


def test_update_product_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 3}

    response = client.put(f"/products/{ID}", json=VALID_PRODUCT_DATA, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_update_product_not_found(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(ProductModel, "get_product", return_value=None)

    response = client.put(f"/products/{ID}", json=VALID_PRODUCT_DATA, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Producto no encontrado"


def test_update_product_exception(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(ProductModel, "get_product", return_value={"name": "Cacahuetes", "stock": 10})
    mocker.patch.object(ProductModel, "update_product", side_effect=PyMongoError("Database error"))

    response = client.put(f"/products/{ID}", json=VALID_PRODUCT_DATA, headers=auth_header)

    assert response.status_code == 500
    assert response.json["err"] == "Ha ocurrido un error en MongoDB: Database error"


def test_handle_product_not_authorized_error(mock_jwt, client, auth_header):
    mock_jwt.return_value = {"role": 3}

    response = client.delete(f"/products/{ID}", headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"


def test_get_product_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(ProductModel, "get_product", return_value=VALID_PRODUCT_DATA)

    response = client.get(f"/products/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_PRODUCT_DATA


def test_get_product_not_found(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(ProductModel, "get_product", return_value=None)

    response = client.get(f"/products/{ID}", headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Producto no encontrado"


def test_delete_product_success(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(ProductModel, "delete_product", return_value=mocker.MagicMock(deleted_count=1))

    response = client.delete(f"/products/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Producto '{ID}' ha sido eliminado de forma satisfactoria"


def test_delete_product_not_found(mocker, client, auth_header, mock_jwt):
    mock_jwt.return_value = {"role": 1}
    mocker.patch.object(ProductModel, "delete_product", return_value=mocker.MagicMock(deleted_count=0))

    response = client.delete(f"/products/{ID}", headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Producto no encontrado"
