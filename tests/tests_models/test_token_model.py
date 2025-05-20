import pytest
import re
from pydantic import ValidationError
from datetime import datetime

from src.models.token_model import TokenModel
from tests.test_helpers import (
    assert_insert_document_template,
    assert_get_all_documents_template,
    assert_get_document_by_id_template,
    assert_delete_document_template,
    assert_update_document_template,
)

ID = "507f1f77bcf86cd799439011"
VALID_DATA = {
    "user_id": ID,
    "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
    "expires_at": 1900757341,
}
INVALID_DATA = {
    "user_id": "507f1f77bcf86cd79943901122",
    "jti": "bb53e637dd-8627-457c-840f-6cae52a12e8b",
    "expires_at": 1729684113900,
}

TOKEN_OBJECT = TokenModel(**VALID_DATA)
TOKEN_OBJECT_UPDATED = TokenModel(
    **{**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"}
)

USER_ID_PATTERN = re.compile("^[a-f0-9]{24}$")
JTI_PATTERN = re.compile(
    "^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
)


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_services.db.refresh_tokens", new=mock_db)
    mocker.patch("src.services.db_services.db.revoked_tokens", new=mock_db)
    mocker.patch("src.services.db_services.db.email_tokens", new=mock_db)
    return mock_db


def test_token_model_valid_data():
    assert isinstance(TOKEN_OBJECT.user_id, str) and USER_ID_PATTERN.match(
        TOKEN_OBJECT.user_id
    )
    assert isinstance(TOKEN_OBJECT.jti, str) and JTI_PATTERN.match(TOKEN_OBJECT.jti)
    assert isinstance(TOKEN_OBJECT.expires_at, datetime)
    assert isinstance(TOKEN_OBJECT.created_at, datetime)


def test_token_model_valid_expires_at_iso8601():
    token = TokenModel(**{**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"})
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
        (VALID_DATA["user_id"], VALID_DATA["jti"], None),
    ],
)
def test_token_validation_errors(user_id, jti, expires_at):
    with pytest.raises(ValidationError):
        TokenModel(user_id=user_id, jti=jti, expires_at=expires_at)


@pytest.mark.parametrize(
    "method",
    [
        TOKEN_OBJECT.insert_refresh_token,
        TOKEN_OBJECT.insert_email_token,
        TOKEN_OBJECT.insert_revoked_token,
    ],
)
def test_insert_tokens(mock_db, method):
    return assert_insert_document_template(mock_db, method)


@pytest.mark.parametrize(
    "method, expected_result",
    [
        (TokenModel.get_refresh_tokens, [VALID_DATA]),
        (TokenModel.get_email_tokens, [VALID_DATA]),
        (TokenModel.get_revoked_tokens, [VALID_DATA]),
    ],
)
def test_get_all_tokens(mock_db, method, expected_result):
    return assert_get_all_documents_template(mock_db, method, expected_result)


@pytest.mark.parametrize(
    "method, expected_result",
    [
        (TokenModel.get_refresh_token_by_token_id, VALID_DATA),
        (TokenModel.get_email_token_by_token_id, VALID_DATA),
        (TokenModel.get_revoked_token_by_token_id, VALID_DATA),
    ],
)
def test_get_token_by_token_id(mock_db, method, expected_result):
    return assert_get_document_by_id_template(mock_db, method, expected_result)


@pytest.mark.parametrize(
    "method, expected_result",
    [
        (
            TOKEN_OBJECT_UPDATED.update_refresh_token,
            {**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"},
        ),
        (
            TOKEN_OBJECT_UPDATED.update_email_token,
            {**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"},
        ),
        (
            TOKEN_OBJECT_UPDATED.update_revoked_token,
            {**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"},
        ),
    ],
)
def test_update_token(mock_db, method, expected_result):
    return assert_update_document_template(mock_db, method, expected_result)


@pytest.mark.parametrize(
    "method",
    [
        TokenModel.delete_refresh_token_by_token_id,
        TokenModel.delete_email_token,
        TokenModel.delete_revoked_token,
    ],
)
def test_delete_token(mock_db, method):
    return assert_delete_document_template(mock_db, method)


@pytest.mark.parametrize(
    "get_by_user_id_function",
    [
        TokenModel.get_refresh_token_by_user_id,
        TokenModel.get_email_token_by_user_id,
    ],
)
def test_get_token_by_user_id(mock_db, get_by_user_id_function):
    mock_db.find_one.return_value = VALID_DATA
    result = get_by_user_id_function(ID)
    assert result == VALID_DATA
    mock_db.find_one.assert_called_once()


def test_delete_refresh_token_by_user_id(mock_db):
    mock_db.delete_one.return_value.deleted_count = 1
    result = TokenModel.delete_refresh_token_by_user_id(ID)
    assert result.deleted_count == 1
    mock_db.delete_one.assert_called_once()


def test_get_email_tokens_by_user_id(mock_db):
    mock_db.find.return_value = [VALID_DATA]
    result = TokenModel.get_email_tokens_by_user_id(ID)
    assert result == [VALID_DATA]
    mock_db.find.assert_called_once()


def test_get_revoked_token_by_jti(mock_db):
    mock_db.find_one.return_value = VALID_DATA
    result = TokenModel.get_revoked_token_by_jti(VALID_DATA["jti"])
    assert result == VALID_DATA
    mock_db.find_one.assert_called_once()
