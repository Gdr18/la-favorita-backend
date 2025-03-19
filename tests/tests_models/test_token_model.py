import pytest
from pydantic import ValidationError
from datetime import datetime
import re

from src.models.token_model import TokenModel

VALID_DATA = {"exp": 1919068218, "jti": "bb53e637-8627-457c-840f-6cae52a12e8b"}

INVALID_DATA = {"exp": 1729684113900, "jti": "bb53e637dd-8627-457c-840f-6cae52a12e8b"}


def test_revoked_token_model_valid():
    regex_jti = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$")
    revoked_token = TokenModel(**VALID_DATA)
    assert regex_jti.match(revoked_token.jti)
    assert isinstance(revoked_token.exp, datetime)


def test_revoked_token_model_invalid_jti_not_match():
    with pytest.raises(ValidationError):
        TokenModel(jti=INVALID_DATA["jti"], exp=VALID_DATA["exp"])


def test_revoked_token_model_invalid_jti_type():
    with pytest.raises(ValidationError):
        TokenModel(jti=123456, exp=VALID_DATA["exp"])


def test_revoked_token_model_invalid_jti_none():
    with pytest.raises(ValidationError):
        TokenModel(jti=None, exp=VALID_DATA["exp"])


def test_revoked_token_model_invalid_jti_empty():
    with pytest.raises(ValidationError):
        TokenModel(jti="", exp=VALID_DATA["exp"])


def test_revoked_token_model_invalid_exp_not_match():
    with pytest.raises(ValidationError):
        TokenModel(jti=VALID_DATA["jti"], exp=INVALID_DATA["exp"])


def test_revoked_token_model_invalid_exp_none():
    with pytest.raises(ValidationError):
        TokenModel(jti=VALID_DATA["jti"], exp=None)


def test_revoked_token_model_invalid_exp_empty():
    with pytest.raises(ValidationError):
        TokenModel(jti=VALID_DATA["jti"], exp="")


def test_revoked_token_model_invalid_exp_type():
    with pytest.raises(ValidationError):
        TokenModel(jti=VALID_DATA["jti"], exp="123456")


def test_revoked_token_model_to_dict():
    revoked_token = (TokenModel(**VALID_DATA)).to_dict()
    assert isinstance(revoked_token, dict)
