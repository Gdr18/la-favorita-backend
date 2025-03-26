import pytest
from pydantic import ValidationError
from flask_jwt_extended import create_access_token

from src.models.product_model import (
    ProductModel,
    get_allowed_values,
    reload_allowed_values,
    _allowed_allergens,
    _allowed_categories,
)

USER_ID = "507f1f77bcf86cd799439011"
PRODUCT_DATA = {
    "name": "Cacahuetes",
    "stock": 345,
    "categories": ["snack", "otro"],
    "allergens": ["cacahuete"],
    "brand": "marca",
    "notes": "notas",
}

ALLERGENS = [
    "cereal",
    "huevo",
    "crustáceo",
    "pescado",
    "cacahuete",
    "soja",
    "lácteo",
    "fruto de cáscara",
    "apio",
    "mostaza",
    "sésamo",
    "sulfito",
    "altramuz",
    "molusco",
]
CATEGORIES = [
    "snack",
    "dulce",
    "fruta",
    "verdura",
    "carne",
    "pescado",
    "lácteo",
    "pan",
    "pasta",
    "arroz",
    "legumbre",
    "huevo",
    "salsa",
    "condimento",
    "especia",
    "aceite",
    "vinagre",
    "bebida alcohólica",
    "bebida no alcohólica",
    "bebida con gas",
    "bebida sin gas",
    "bebida alcohólica fermentada",
    "bebida energética",
    "bebida isotónica",
    "limpieza",
    "otro",
]


@pytest.fixture
def mock_db_settings(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.settings", new=mock_db)
    return mock_db


@pytest.fixture
def mock_db_products(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.products", new=mock_db)
    return mock_db


def test_get_allowed_values(mock_db_settings):
    mock_db_settings.find_one.return_value = {"values": ["value1", "value2"]}
    result = get_allowed_values("test_name")
    assert result == ["value1", "value2"]
    mock_db_settings.find_one.assert_called_once_with({"name": "test_name"}, {"name": 0, "_id": 0})


def test_reload_allowed_values(mock_db_settings):
    mock_db_settings.find_one.side_effect = [{"values": ALLERGENS}, {"values": CATEGORIES}]

    reload_allowed_values()

    assert _allowed_allergens == ALLERGENS
    assert _allowed_categories == CATEGORIES


def test_product_validate_allergens_none():
    product = ProductModel(
        name="Cacahuetes", stock=345, categories=["snack", "otro"], allergens=None, brand="marca", notes="notas"
    )
    assert product.allergens is None


def test_product_validate_values_in_list():
    product = ProductModel(**PRODUCT_DATA)

    assert all(isinstance(item, str) for item in product.categories)
    assert all(isinstance(item, str) for item in product.allergens)
    assert all(category in _allowed_categories for category in product.categories)
    assert all(allergen in _allowed_allergens for allergen in product.allergens)


@pytest.mark.parametrize(
    "name, stock, categories, allergens, brand, notes",
    [
        (123, 345, ["snack"], ["cacahuete"], "marca", "notas"),
        ("", 345, ["snack"], ["cacahuete"], "marca", "notas"),
        ("a" * 51, 345, ["snack"], ["cacahuete"], "marca", "notas"),
        ("Cacahuetes", 345, "bebida", None, "marca", "notas"),
        ("Cacahuetes", 345, ["snack"], "cacahuete", "marca", "notas"),
        ("Cacahuetes", 345, [], ["cacahuete"], "marca", "notas"),
        ("Cacahuetes", 345, ["snack"], [], "marca", "notas"),
        ("Cacahuetes", 345, [1234], ["cacahuete"], "marca", "notas"),
        ("Cacahuetes", 345, ["snack"], [1234], "marca", "notas"),
        ("Cacahuetes", 345, [""], ["cacahuete"], "marca", "notas"),
        ("Cacahuetes", -345, ["snack"], ["cacahuete"], "marca", "notas"),
        ("Cacahuetes", "hola", ["snack"], ["cacahuete"], "marca", "notas"),
        ("Cacahuetes", 345, ["snack"], ["cacahuete"], "a" * 51, "notas"),
        ("Cacahuetes", 345, ["snack"], ["cacahuete"], 234, "notas"),
        ("Cacahuetes", 345, ["snack"], ["cacahuete"], "", "notas"),
        ("Cacahuetes", 345, ["snack"], ["cacahuete"], "marca", "a" * 501),
        ("Cacahuetes", 345, ["snack"], ["cacahuete"], "marca", ""),
    ],
)
def test_product_validation_errors(name, stock, categories, allergens, brand, notes):
    with pytest.raises(ValidationError):
        ProductModel(name=name, stock=stock, categories=categories, allergens=allergens, brand=brand, notes=notes)


def test_product_checking_in_list_invalid_values():
    with pytest.raises(ValueError):
        ProductModel.checking_in_list("categories", ["invalid1", "invalid2"], ["snack"])
    with pytest.raises(ValueError):
        ProductModel.checking_in_list("allergens", ["invalid3", "invalid4"], ["cacahuete"])


def test_insert_product(mock_db_products):
    mock_db_products.insert_one.return_value.inserted_id = USER_ID
    result = ProductModel(**PRODUCT_DATA).insert_product()
    assert result.inserted_id == USER_ID


def test_get_products(mock_db_products):
    mock_cursor = mock_db_products.find.return_value
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = [PRODUCT_DATA]
    result = ProductModel.get_products(1, 10)
    assert result == [PRODUCT_DATA]


def test_get_product(mock_db_products):
    mock_db_products.find_one.return_value = PRODUCT_DATA
    result = ProductModel.get_product(USER_ID)
    assert result == PRODUCT_DATA


def test_update_product(mock_db_products):
    new_data = {**PRODUCT_DATA, "name": "new_value"}
    mock_db_products.find_one_and_update.return_value = new_data
    result = ProductModel(**new_data).update_product(USER_ID)
    assert result["name"] == "new_value"


def test_update_product_stock_by_name(mock_db_products):
    mock_db_products.find_one_and_update.return_value = {**PRODUCT_DATA, "stock": 100}
    item_data = {
        "name": "Plato 1",
        "ingredients": [{"name": "Cacahuetes", "allergens": ["cereal", "huevo"], "waste": 10}],
        "qty": 10,
        "price": 10.99,
    }
    result = ProductModel.update_product_stock_by_name([item_data])
    assert result[0]["stock"] == 100


def test_delete_product(mock_db_products):
    mock_db_products.delete_one.return_value.deleted_count = 1
    result = ProductModel.delete_product(USER_ID)
    assert result.deleted_count == 1
