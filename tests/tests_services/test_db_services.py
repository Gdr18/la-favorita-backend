import pytest
from pymongo.errors import ConnectionFailure
from pymongo.database import Database

from src.services.db_services import db_connection
from tests.test_helpers import app


def test_db_connection_success(mocker):
    mock_db_client = mocker.patch("src.services.db_services.MongoClient")
    mock_database = mocker.MagicMock(spec=Database)
    mock_client_instance = mock_db_client.return_value
    mock_client_instance.__getitem__.return_value = mock_database

    result = db_connection()

    assert result == mock_database
    mock_db_client.assert_called_once()


def test_db_connection_failure(app, mocker):
    with app.app_context():
        error = ConnectionFailure("Database connection error")
        cl = mocker.patch("src.services.db_services.get_client", side_effect=error)

        result, status_code = db_connection()

        assert status_code == 500
        assert result.json == {"err": f"Error de conexión con MongoDB: {error}"}
        cl.assert_called_once()
