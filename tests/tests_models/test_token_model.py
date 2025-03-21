import pytest
from pydantic import ValidationError
from datetime import datetime
import re

from src.models.token_model import TokenModel

VALID_DATA = {"user_id": "507f1f77bcf86cd799439011", "jti": "bb53e637-8627-457c-840f-6cae52a12e8b", "expires_at": 1919068218}

INVALID_DATA = {"user_id": "507f1f77bcf86cd79943901133", "jti": "bb53e637dd-8627-457c-840f-6cae52a12e8b", "expires_at": 1729684113900}


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.refresh_tokens", new=mock_db)
    mocker.patch("src.services.db_services.db.revoked_tokens", new=mock_db)
    mocker.patch("src.services.db_services.db.email_tokens", new=mock_db)
    return mock_db

#
# @pytest.fixture
# def mock_db_refresh_tokens(mocker):
#     mock_db_refresh_tokens = mocker.MagicMock()
#     mocker.patch("src.services.db_services.db.refresh_tokens", new=mock_db_refresh_tokens)
#     return mock_db_refresh_tokens
#
#
# @pytest.fixture
# def mock_db_revoked_tokens(mocker):
#     mock_db_revoked_tokens = mocker.MagicMock()
#     mocker.patch("src.services.db_services.db.revoked_tokens", new=mock_db_revoked_tokens)
#     return mock_db_revoked_tokens
#
#
# @pytest.fixture
# def mock_db_email_tokens(mocker):
#     mock_db_email_tokens = mocker.MagicMock()
#     mocker.patch("src.services.db_services.db.email_tokens", new=mock_db_email_tokens)
#     return mock_db_email_tokens
#


def test_revoked_token_model_valid_expires_at_timestamp():
    regex_jti = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$")
    token = TokenModel(**VALID_DATA)
    assert regex_jti.match(token.jti)
    assert isinstance(token.expires_at, datetime)


def test_revoked_token_model_valid_expires_at_iso8601():
    token = TokenModel(user_id=VALID_DATA["user_id"], jti=VALID_DATA["jti"], expires_at="2025-03-22T14:22:05+01:00")

    assert isinstance(token.expires_at, datetime)


@pytest.mark.parametrize(
    "user_id, jti, expires_at",
    [
        (VALID_DATA["user_id"], INVALID_DATA["jti"], VALID_DATA["expires_at"]),
        (INVALID_DATA["user_id"], VALID_DATA["jti"], VALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], VALID_DATA["jti"], INVALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], VALID_DATA["jti"], "2025-03-20T14:29:00+01:00"),
        (VALID_DATA["user_id"], VALID_DATA["jti"], ""),
        ("", VALID_DATA["jti"], VALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], "", VALID_DATA["expires_at"]),
        (None, VALID_DATA["jti"], VALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], None, VALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], VALID_DATA["jti"], None)
    ]
)
def test_token_validation_errors(user_id, jti, expires_at):
    with pytest.raises(ValidationError):
        TokenModel(user_id=user_id, jti=jti, expires_at=expires_at)


@pytest.mark.parametrize(
    "collection, insert_function, get_all_function, get_by_token_id, update_function, delete_function",
    [
        ("refresh_tokens", TokenModel(**VALID_DATA).insert_refresh_token, TokenModel.get_refresh_tokens, TokenModel.get_refresh_token_by_token_id, TokenModel(**VALID_DATA).update_refresh_token, TokenModel.delete_refresh_token_by_token_id),
        ("email_tokens", TokenModel(**VALID_DATA).insert_email_token, TokenModel.get_email_tokens, TokenModel.get_email_token_by_token_id, TokenModel(**VALID_DATA).update_email_token, TokenModel.delete_email_token),
        ("revoked_tokens", TokenModel(**VALID_DATA).insert_revoked_token, TokenModel.get_revoked_tokens, TokenModel.get_revoked_token_by_token_id, TokenModel(**VALID_DATA).update_revoked_token, TokenModel.delete_revoked_token)
    ]
)
def test_token_operations(mock_db, collection, insert_function, get_all_function, get_by_token_id, update_function, delete_function):
    mock_db.insert_one.return_value.inserted_id = VALID_DATA["user_id"]
    result = insert_function()
    assert result.inserted_id == VALID_DATA["user_id"]

    mock_cursor = mock_db.find.return_value
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = [VALID_DATA]
    result = get_all_function(1, 10)
    assert isinstance(result, list)
    assert result == [VALID_DATA]

    mock_db.find_one.return_value = VALID_DATA

    result = get_by_token_id("507f1f77bcf86cd799439011")

    assert isinstance(result, dict)
    assert result == VALID_DATA

    mock_db.find_one_and_update.return_value = VALID_DATA
    result = update_function("507f1f77bcf86cd799439011")
    assert result == VALID_DATA

    mock_db.delete_one.return_value.deleted_count = 1
    result = delete_function("507f1f77bcf86cd799439011")
    assert result.deleted_count == 1
