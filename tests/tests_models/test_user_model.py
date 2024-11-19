import pytest
import re
from pydantic import ValidationError
from src.models.user_model import UserModel


bcrypt_pattern = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")


# Tests validate name
def test_user_validate_name_valid():
    user = UserModel(
        name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1
    )
    assert isinstance(user.name, str) and 1 <= len(user.name) <= 50


def test_user_validate_name_none():
    with pytest.raises(ValidationError):
        UserModel(
            name=None, email="john.doe@example.com", password="ValidPass123!", role=1
        )


def test_user_validate_name_empty():
    with pytest.raises(ValidationError):
        UserModel(
            name="", email="john.doe@example.com", password="ValidPass123!", role=1
        )


def test_user_validate_name_too_long():
    with pytest.raises(ValidationError):
        UserModel(
            name="J" * 51,
            email="john.doe@example.com",
            password="ValidPass123!",
            role=1,
        )


# Tests validate email
def test_user_validate_email_valid():
    user = UserModel(
        name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1
    )
    assert isinstance(user.email, str) and 5 <= len(user.email) <= 100


def test_user_validate_email_none():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email=None, password="ValidPass123!", role=1)


def test_user_validate_email_empty():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="", password="ValidPass123!", role=1)


def test_user_validate_email_too_long():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="j" * 101, password="ValidPass123!", role=1)


def test_user_validate_email_invalid_type():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email=123456, password="ValidPass123!", role=1)


def test_user_validate_email_invalid():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe", password="ValidPass123!", role=1)


# Tests validate password
def test_user_validate_password_valid():
    user = UserModel(
        name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1
    )
    assert bcrypt_pattern.match(user.password) is not None


def test_user_validate_password_invalid_length():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe", email="john.doe@example.com", password="Short1!", role=1
        )


def test_user_validate_password_no_uppercase():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="nouppercase1!",
            role=1,
        )


def test_user_validate_password_no_lowercase():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="NOLOWERCASE1!",
            role=1,
        )


def test_user_validate_password_no_digit():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="NoDigitPass!",
            role=1,
        )


def test_user_validate_password_no_special_char():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="NoSpecialChar1",
            role=1,
        )


def test_user_validate_password_bcrypt():
    user = UserModel(
        name="John Doe",
        email="john.doe@example.com",
        password="$2b$12$03X1igkfTyrZUNPgsn2c1urHqTJl4MicGFrMQ2lNb9b2qbUBN9e0u",
    )
    assert bcrypt_pattern.match(user.password) is not None


# Tests validate role
def test_user_validate_role_type():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="ValidPass123!",
            role="hola",
        )


def test_user_validate_role_superate_max():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="ValidPass123!",
            role=4,
        )


def test_user_validate_role_superate_min():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="ValidPass123!",
            role=0,
        )


# Tests validate phone
def test_user_validate_phone_valid():
    user = UserModel(
        name="John Doe",
        email="john.doe@example.com",
        password="ValidPass123!",
        role=1,
        phone="+34666666666",
    )
    phone_pattern = re.compile(r"^\+\d{9,15}$")
    assert phone_pattern.match(user.phone)


def test_user_validate_phone_valid_none():
    user = UserModel(
        name="John Doe",
        email="john.doe@example.com",
        password="ValidPass123!",
        role=1,
        phone=None,
    )
    assert user.phone is None


def test_user_validate_phone_not_match():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="ValidPass123!",
            role=1,
            phone="123-456-7890",
        )


def test_user_validate_phone_type():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="ValidPass123!",
            role=1,
            phone=1237890,
        )


# Tests validate basket/addresses
def test_user_validate_addresses_basket_valid():
    user = UserModel(
        name="John Doe",
        email="john.doe@example.com",
        password="ValidPass123!",
        role=1,
        basket=[{"item": 1}],
        addresses=[{"street": "Calle Falsa 123"}],
    )
    assert all(isinstance(item, dict) for item in user.basket) is True
    assert all(isinstance(item, dict) for item in user.addresses) is True


def test_user_validate_addresses_basket_non_list_or_none():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="ValidPass123!",
            role=1,
            basket="item1",
            addresses=5235634,
        )


def test_user_validate_addresses_basket_list_of_non_dicts():
    with pytest.raises(ValidationError):
        UserModel(
            name="John Doe",
            email="john.doe@example.com",
            password="ValidPass123!",
            role=1,
            basket=[213122],
            addresses=["+123ABC7890"],
        )


def test_user_validate_addresses_basket_valid():
    user = UserModel(
        name="John Doe",
        email="john.doe@example.com",
        password="ValidPass123!",
        role=1,
        basket=[{"item": "item1"}],
        addresses=None,
    )
    assert (
        all(isinstance(item, dict) for item in user.basket) is True
        and user.addresses is None
    )


def test_user_to_dict():
    user_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "password": "Password123!",
        "role": 2,
    }
    user = UserModel(**user_data)
    user_dict = user.to_dict()
    assert isinstance(user_dict, dict)
