import pytest
from pymongo.errors import ConnectionFailure
from pymongo.database import Database

from src.services.db_services import db_connection


@pytest.fixture
def mock_db_client(mocker):
    mock_client = mocker.patch("src.services.db_services.MongoClient")
    return mock_client


def test_db_connection_success(mock_db_client, mocker):
    mock_client_instance = mock_db_client.return_value
    mock_database = mocker.MagicMock(spec=Database)
    mock_client_instance.__getitem__.return_value = mock_database
    result = db_connection()
    assert result == mock_database
    mock_client_instance.__getitem__.assert_called_once_with("test_la_favorita")


def test_db_connection_failure(mocker, mock_db_client):
    error = ConnectionFailure("Database connection error")
    mock_client_instance = mock_db_client.return_value
    mock_client_instance.__getitem__.side_effect = error
    mock_handle_exception = mocker.patch("src.services.db_services.handle_mongodb_exception")
    db_connection()
    mock_handle_exception.assert_called_once_with(error)
