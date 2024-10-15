import pytest
from pydantic import ValidationError

from src.models.product_model import ProductModel, get_allowed_values


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch('src.utils.db_utils.db.settings', new=mock_db)
    return mock_db


def test_get_allowed_values(mock_db):
    mock_db.find_one.return_value = {"values": ["value1", "value2"]}
    result = get_allowed_values("test_name")
    assert result == ["value1", "value2"]
    mock_db.find_one.assert_called_once_with({"name": "test_name"}, {"name": 0, "_id": 0})


def test_product_validate_categories_allergens_non_list_or_none():
    with pytest.raises(ValidationError):
        ProductModel(name="Patatas", stock=345, categories=None)
    with pytest.raises(ValidationError):
        ProductModel(name="Patatas", stock=345, categories=["snack"], allergens="cacahuete")


def test_product_validate_categories_empty_list():
    with pytest.raises(ValidationError):
        ProductModel(name="Cacahuetes", stock=345, categories=[], allergens=["cacahuete"], brand="marca", notes="notas")


def test_product_validate_categories_allergens_list_of_non_strs():
    with pytest.raises(ValidationError):
        ProductModel(name="Cacahuetes", stock=345, categories=[1234], allergens=["cacahuete"], brand="marca", notes="notas")


def test_product_validate_categories_allergens_list_of_empty_strs():
    with pytest.raises(ValidationError):
        ProductModel(name="Cacahuetes", stock=345, categories=[""], allergens=["cacahuete"], brand="marca", notes="notas")


def test_product_validate_categories_allergens_valid():
    product = ProductModel(name="Cacahuetes", stock=345, categories=["snack", "otro"], allergens=["cacahuete"], brand="marca", notes="notas")
    assert isinstance(product.categories, list)
    assert isinstance(product.allergens, list)
    assert all(isinstance(item, str) for item in product.categories)
    assert all(isinstance(item, str) for item in product.allergens)


def test_product_validate_allergens_valid_none():
    product = ProductModel(name="Cacahuetes", stock=345, categories=["snack", "otro"], allergens=None, brand="marca", notes="notas")
    assert product.allergens is None


def test_product_checking_in_list_invalid_values():
    with pytest.raises(ValueError):
        ProductModel.checking_in_list("categories", ["invalid1", "invalid2"], ["snack"])
    with pytest.raises(ValueError):
        ProductModel.checking_in_list("allergens", ["invalid3", "invalid4"], ["cacahuete"])


def test_product_to_dict():
    product = ProductModel(name="Cacahuetes", stock=345, categories=["snack", "otro"], allergens=["cacahuete"], brand="marca", notes="notas")
    product_dict = product.to_dict()
    assert isinstance(product_dict, dict)
