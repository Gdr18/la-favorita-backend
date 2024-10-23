import pytest
import re
import pendulum
from pydantic import ValidationError

from src.models.revoked_token_model import RevokedTokenModel

VALID_DATA = {
    "exp": pendulum.datetime(2024, 12, 31, 23, 59, 59),
    "jti": "bb53e637-8627-457c-840f-6cae52a12e8b"
}

INVALID_DATA = {
    "exp": 1729684113900,
    "jti": "bb53e637dd-8627-457c-840f-6cae52a12e8b"
}


def test_revoked_token_model_valid():
    regex_jti = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$')
    revoked_token = RevokedTokenModel(**VALID_DATA)
    assert regex_jti.match(revoked_token.jti)
    assert isinstance(revoked_token.exp, pendulum.DateTime)


def test_revoked_token_model_invalid_jti():
    with pytest.raises(ValidationError):
        RevokedTokenModel(jti=INVALID_DATA["jti"], exp=VALID_DATA["exp"])


def test_revoked_token_model_invalid_exp():
    with pytest.raises(ValidationError):
        RevokedTokenModel(jti=VALID_DATA["jti"], exp=INVALID_DATA["exp"])


def test_revoked_token_model_to_dict():
    revoked_token = (RevokedTokenModel(**VALID_DATA)).to_dict()
    assert isinstance(revoked_token, dict)
    assert revoked_token == VALID_DATA
