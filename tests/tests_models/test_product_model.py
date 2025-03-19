import pytest
from pydantic import ValidationError
from flask_jwt_extended import create_access_token
from pymongo.results import InsertOneResult

from src.models.product_model import (
    ProductModel,
    get_allowed_values,
    reload_allowed_values,
    _allowed_allergens,
    _allowed_categories,
)


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
    mock_db_settings.find_one.side_effect = [
        {
            "values": [
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
        },
        {
            "values": [
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
        },
    ]

    reload_allowed_values()

    assert _allowed_allergens == [
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
    assert _allowed_categories == [
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


@pytest.mark.parametrize(
    "name, stock, categories, allergens, brand, notes",
    [
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
        ("Cacahuetes", 345, ["snack"], ["cacahuete"], "a" * 51, "notas"),
        ("Cacahuetes", 345, ["snack"], ["cacahuete"], "marca", "a" * 501),
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


def test_product_validate_allergens_none():
    product = ProductModel(
        name="Cacahuetes", stock=345, categories=["snack", "otro"], allergens=None, brand="marca", notes="notas"
    )
    assert product.allergens is None


def test_product_validate_values_in_list():
    product = ProductModel(
        name="Cacahuetes",
        stock=345,
        categories=["snack", "otro"],
        allergens=["cacahuete"],
        brand="marca",
        notes="notas",
    )

    assert all(isinstance(item, str) for item in product.categories)
    assert all(isinstance(item, str) for item in product.allergens)
    assert all(category in _allowed_categories for category in product.categories)
    assert all(allergen in _allowed_allergens for allergen in product.allergens)


def test_insert_product(mock_db_products):
    product_data = {
        "name": "Cacahuetes",
        "stock": 345,
        "categories": ["snack", "otro"],
        "allergens": ["cacahuete"],
        "brand": "marca",
        "notes": "notas",
    }
    product = ProductModel(**product_data)

    mock_db_products.insert_one.return_value = InsertOneResult(
        inserted_id="507f1f77bcf86cd799439011", acknowledged=True
    )

    result = product.insert_product()

    assert isinstance(result, InsertOneResult)
    assert result.inserted_id == "507f1f77bcf86cd799439011"
    assert result.acknowledged is True


def test_get_products(mock_db_products):
    product_data = {
        "name": "Cacahuetes",
        "stock": 345,
        "categories": ["snack", "otro"],
        "allergens": ["cacahuete"],
        "brand": "marca",
        "notes": "notas",
    }

    mock_cursor = mock_db_products.find.return_value
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = [product_data]

    result = ProductModel.get_products(0, 10)

    assert isinstance(result, list)
    assert result == [product_data]


def test_get_product(mock_db_products):
    mock_db_products.find_one.return_value = {
        "name": "Cacahuetes",
        "stock": 345,
        "categories": ["snack", "otro"],
        "allergens": ["cacahuete"],
        "brand": "marca",
        "notes": "notas",
    }

    result = ProductModel.get_product("507f1f77bcf86cd799439011")

    assert isinstance(result, dict)


def test_update_product(mock_db_products):
    product_data = {
        "name": "Cacahuetes",
        "stock": 345,
        "categories": ["snack", "otro"],
        "allergens": ["cacahuete"],
        "brand": "marca",
        "notes": "notas",
    }
    product = ProductModel(**product_data)

    mock_db_products.find_one_and_update.return_value = {**product_data, "name": "new_value"}

    result = product.update_product("507f1f77bcf86cd799439011")

    assert isinstance(result, dict)
    assert result["name"] == "new_value"


def test_update_product_stock_by_name(mock_db_products):
    product_data = {
        "name": "Cacahuetes",
        "stock": 345,
        "categories": ["snack", "otro"],
        "allergens": ["cacahuete"],
        "brand": "marca",
        "notes": "notas",
    }
    product = ProductModel(**product_data)

    mock_db_products.find_one_and_update.return_value = {**product_data, "stock": 100}

    item_data = {
        "name": "Plato 1",
        "ingredients": [{"name": "Cacahuetes", "allergens": ["cereal", "huevo"], "waste": 10}],
        "qty": 10,
        "price": 10.99,
    }

    result = product.update_product_stock_by_name([item_data])

    assert isinstance(result, list)
    assert result[0]["stock"] == 100


def test_delete_product(mock_db_products):
    mock_db_products.delete_one.return_value.deleted_count = 1

    result = ProductModel.delete_product("507f1f77bcf86cd799439011")

    assert result.deleted_count == 1
