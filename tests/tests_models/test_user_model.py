import pytest
import re
from pydantic import ValidationError
from src.models.user_model import UserModel


# Tests validate password
bcrypt_pattern = re.compile(r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$')


def test_validate_password_valid():
    user = UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1)
    assert bcrypt_pattern.match(user.password) is not None


def test_validate_password_invalid_length():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="Short1!", role=1)


def test_validate_password_no_uppercase():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="nouppercase1!", role=1)


def test_validate_password_no_lowercase():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="NOLOWERCASE1!", role=1)


def test_validate_password_no_digit():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="NoDigitPass!", role=1)


def test_validate_password_no_special_char():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="NoSpecialChar1", role=1)


def test_validate_password_bcrypt():
    user = UserModel(name="John Doe", email="john.doe@example.com", password="$2b$12$03X1igkfTyrZUNPgsn2c1urHqTJl4MicGFrMQ2lNb9b2qbUBN9e0u")
    assert bcrypt_pattern.match(user.password) is not None


# Tests validate phone
def test_validate_phone_valid():
    user = UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1, phone="+34666666666")
    phone_pattern = re.compile(r'^\+\d{9,15}$')
    assert phone_pattern.match(user.phone)


def test_validate_phone_valid_none():
    user = UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1, phone=None)
    assert user.phone is None


def test_validate_phone_invalid_format():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1, phone="123-456-7890")


def test_validate_phone_too_short():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1, phone="+123")


def test_validate_phone_too_long():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1, phone="+12345678901234567890")


def test_validate_phone_non_numeric():
    with pytest.raises(ValidationError):
        UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass123!", role=1, phone="+123ABC7890")


def test_to_dict():
    user_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "password": "Password123!",
        "role": 2,
        "phone": "+34123456789",
        "addresses": ["123 Main St", "456 Elm St"],
        "basket": ["item1", "item2"]
    }

    user = UserModel(**user_data)
    user_dict = user.to_dict()

    assert isinstance(user_dict, dict) is True

