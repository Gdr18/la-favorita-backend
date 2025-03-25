import pytest
import re
from pydantic import ValidationError
from email_validator import validate_email
from datetime import datetime

from src.models.user_model import UserModel


BCRYPT_PATTERN = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*_-]).{8,}$")
PHONE_PATTERN = re.compile(r"^\+\d{9,15}$")

VALID_DATA_EMAIL = {
    "name": "John Doe",
    "email": "john.doe@outlook.com",
    "password": "ValidPass123!",
    "role": 1,
    "phone": "+34666666666",
    "basket": [{"name": "galletas", "qty": 1, "price": 3.33}],
    "addresses": [{"line_one": "Calle Falsa 123", "postal_code": "12345"}],
}

VALID_DATA_GOOGLE = {
    "name": "John Doe",
    "email": "john.doe@google.com",
    "auth_provider": "google",
    "role": 1,
    "phone": "+34666666666",
    "basket": [{"name": "galletas", "qty": 1, "price": 3.33}],
    "addresses": [{"line_one": "Calle Falsa 123", "postal_code": "12345"}],

}


def test_user_valid_data_email():
    user = UserModel(**VALID_DATA_EMAIL)
    assert isinstance(user.name, str) and 1 <= len(user.name) <= 50
    assert isinstance(user.email, str) and 5 <= len(user.email) <= 100 and validate_email(user.email)
    assert BCRYPT_PATTERN.match(user.password) or re.match(PASSWORD_PATTERN, user.password)
    assert user.phone is None or PHONE_PATTERN.match(user.phone)
    assert user.basket is None or (isinstance(user.basket, list) and all(isinstance(item, dict) for item in user.basket))
    assert user.addresses is None or (isinstance(user.addresses, list) and all(isinstance(item, dict) for item in user.addresses))
    assert 0 <= user.role <= 3
    assert user.confirmed is False
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.expires_at, datetime)


def test_user_valid_data_google():
    user = UserModel(**VALID_DATA_GOOGLE)
    assert isinstance(user.name, str) and 1 <= len(user.name) <= 50
    assert isinstance(user.email, str) and 5 <= len(user.email) <= 100 and validate_email(user.email)
    assert user.password is None
    assert user.phone is None or PHONE_PATTERN.match(user.phone)
    assert user.basket is None or (
                isinstance(user.basket, list) and all(isinstance(item, dict) for item in user.basket))
    assert user.addresses is None or (
                isinstance(user.addresses, list) and all(isinstance(item, dict) for item in user.addresses))
    assert 0 <= user.role <= 3
    assert user.confirmed is True
    assert isinstance(user.created_at, datetime)
    assert user.expires_at is None


def test_user_validate_password_bcrypt():
    user = UserModel(name=VALID_DATA_EMAIL["name"], email=VALID_DATA_EMAIL["email"], password="$2a$10$JN3FJiqzSy22GplwwrCbuuf/EwUj3Oa3yhi3r.1HyRL7FxOAcvSGu")
    assert user.password == "$2a$10$JN3FJiqzSy22GplwwrCbuuf/EwUj3Oa3yhi3r.1HyRL7FxOAcvSGu"


@pytest.mark.parametrize("name, email, password, role, auth_provider, phone, basket, addresses", [
    (None, VALID_DATA_EMAIL["email"], VALID_DATA_EMAIL["password"], VALID_DATA_EMAIL["role"], "email", None, None, None),
    ("", VALID_DATA_EMAIL["email"], VALID_DATA_EMAIL["password"], VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], None, VALID_DATA_EMAIL["password"], VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], "gador@e.eu", VALID_DATA_EMAIL["password"], VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], None, VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], "short1!", VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], "nouppercase1!", VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], "NOLOWERCASE1!", VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], "NoDigitPass!", VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], "NoSpecialChar1", VALID_DATA_EMAIL["role"], "email", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], VALID_DATA_EMAIL["password"], 4, "email", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], VALID_DATA_EMAIL["password"], VALID_DATA_EMAIL["role"], "hola", None, None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], VALID_DATA_EMAIL["password"], VALID_DATA_EMAIL["role"], "email", "+1234567890", None, None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], VALID_DATA_EMAIL["password"], VALID_DATA_EMAIL["role"], "email", None, ["hola"], None),
    (VALID_DATA_EMAIL["name"], VALID_DATA_EMAIL["email"], VALID_DATA_EMAIL["password"], VALID_DATA_EMAIL["role"], "email", None, None, [123456]),
])
def test_user_validation_error(name, email, password, role, auth_provider, phone, basket, addresses):
    with pytest.raises(ValidationError):
        UserModel(
            name=name, email=email, password=password, role=role, auth_provider=auth_provider, phone=phone, basket=basket, addresses=addresses
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


def test_user_validate_addresses_none():
    user = UserModel(
        name="John Doe",
        email="john.doe@google.com",
        password="ValidPass123!",
        role=1,
        basket=[{"name": "galletas", "qty": 1, "price": 3.33}],
        addresses=None,
    )
    assert user.addresses is None
