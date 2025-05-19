import pytest
import json
from pymongo.errors import PyMongoError

from src.models.order_model import OrderModel
from src.models.product_model import ProductModel
from tests.test_helpers import app, client, auth_header


ID = "507f1f77bcf86cd799439011"
VALID_ORDER_DATA = {
    "user_id": ID,
    "items": [
        {
            "name": "pizza",
            "qty": 2,
            "price": 10.0,
            "ingredients": [
                {"name": "tomato", "waste": 0},
            ],
        }
    ],
    "type_order": "collect",
    "payment": "card",
    "total_price": 20.0,
    "state": "cooking",
}


@pytest.fixture
def mock_get_jwt(mocker):
    return mocker.patch("src.routes.orders_route.get_jwt")


@pytest.fixture
def mock_get_order(mocker):
    return mocker.patch.object(OrderModel, "get_order")


@pytest.fixture
def mock_update_order(mocker):
    return mocker.patch.object(OrderModel, "update_order")


@pytest.fixture
def mock_delete_order(mocker):
    return mocker.patch.object(OrderModel, "delete_order")


@pytest.mark.parametrize(
    "url, method",
    [
        ("/orders/", "get"),
        ("/orders/users/507f1f77bcf86cd799439011", "get"),
        ("/orders/507f1f77bcf86cd799439011", "put"),
        ("/orders/507f1f77bcf86cd799439011", "get"),
        ("/orders/507f1f77bcf86cd799439011", "delete"),
    ],
)
def test_not_authorized_error(mock_get_jwt, client, auth_header, url, method):
    mock_get_jwt.return_value = {"role": 3, "sub": "507f1f77bcf86cd799439012"}

    if method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json={"state": "cooking"}, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)

    assert response.status_code == 401
    assert response.json["err"] == "El token no está autorizado a acceder a esta ruta"
    mock_get_jwt.assert_called_once()


@pytest.mark.parametrize(
    "url, method",
    [
        ("/orders/507f1f77bcf86cd799439011", "put"),
        ("/orders/507f1f77bcf86cd799439011", "get"),
        ("/orders/507f1f77bcf86cd799439011", "delete"),
    ],
)
def test_order_not_found_error(
    mocker,
    client,
    auth_header,
    mock_get_jwt,
    mock_get_order,
    mock_delete_order,
    url,
    method,
):
    mock_get_jwt.return_value = {"role": 1}

    if method in ["get", "put"]:
        mock_get_order.return_value = None
    else:
        mock_delete_order.return_value = mocker.MagicMock(deleted_count=0)

    if method == "put":
        response = client.put(
            f"/orders/{ID}", json={"state": "cooking"}, headers=auth_header
        )
    elif method == "get":
        response = client.get(f"/orders/{ID}", headers=auth_header)
    elif method == "delete":
        response = client.delete(f"/orders/{ID}", headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "Orden no encontrado"
    mock_get_jwt.assert_called_once()
    (
        mock_get_order.assert_called_once()
        if method != "delete"
        else mock_delete_order.assert_called_once()
    )


def test_add_order_success(mocker, client, auth_header):
    mock_db = mocker.patch.object(
        OrderModel,
        "insert_order",
        return_value=mocker.MagicMock(inserted_id=ID),
    )

    response = client.post("/orders/", json=VALID_ORDER_DATA, headers=auth_header)

    assert response.status_code == 201
    assert (
        response.json["msg"] == f"Orden '{ID}' ha sido insertado de forma satisfactoria"
    )
    mock_db.assert_called_once()


def test_get_orders_success(mocker, client, auth_header):
    mock_db = mocker.patch.object(
        OrderModel, "get_orders", return_value=[VALID_ORDER_DATA]
    )

    response = client.get("/orders/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_ORDER_DATA]
    mock_db.assert_called_once()


def test_get_user_orders_success(mocker, client, auth_header):
    mock_db = mocker.patch.object(
        OrderModel, "get_orders_by_user_id", return_value=[VALID_ORDER_DATA]
    )

    response = client.get(f"/orders/users/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_ORDER_DATA]
    mock_db.assert_called_once()


def test_update_order_success(
    mocker, client, auth_header, mock_get_order, mock_update_order
):
    mock_get_order.return_value = VALID_ORDER_DATA
    mock_update_order.return_value = {**VALID_ORDER_DATA, "state": "ready"}
    mock_update_product = mocker.patch.object(
        ProductModel,
        "update_product_stock_by_name",
        return_value=[
            {
                "name": "Cacahuetes",
                "stock": 345,
                "categories": ["snack", "otro"],
                "allergens": ["cacahuete"],
                "brand": "marca",
                "notes": "notas",
            }
        ],
    )

    response = client.put(f"/orders/{ID}", json={"state": "ready"}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_ORDER_DATA, "state": "ready"}
    mock_get_order.assert_called_once()
    mock_update_order.assert_called_once()
    mock_update_product.assert_called_once()


def test_update_order_exception(client, auth_header, mock_get_order, mock_update_order):
    mock_get_order.return_value = VALID_ORDER_DATA
    mock_update_order.side_effect = PyMongoError("Database error")

    response = client.put(f"/orders/{ID}", json={"state": "ready"}, headers=auth_header)

    assert response.status_code == 500
    assert response.json["err"] == "Ha ocurrido un error en MongoDB: Database error"
    mock_get_order.assert_called_once()
    mock_update_order.assert_called_once()


def test_get_order_success(client, auth_header, mock_get_order):
    mock_get_order.return_value = VALID_ORDER_DATA

    response = client.get(f"/orders/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_ORDER_DATA
    mock_get_order.assert_called_once()


def test_delete_order_success(mocker, client, auth_header, mock_delete_order):
    mock_delete_order.return_value = mocker.MagicMock(deleted_count=1)

    response = client.delete(f"/orders/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert (
        response.json["msg"] == f"Orden '{ID}' ha sido eliminado de forma satisfactoria"
    )
    mock_delete_order.assert_called_once()
