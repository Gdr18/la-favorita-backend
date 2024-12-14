import pytest
from pymongo.errors import ConnectionFailure

from config import DATABASE_URI
from run import app as real_app
from src.services.db_services import db_connection


@pytest.fixture
def app():
    real_app.testing = True
    return real_app


@pytest.fixture
def mock_mongo_client(mocker):
    return mocker.patch("src.utils.db_utils.MongoClient")


def test_db_connection_success(mock_mongo_client):
    mock_client_instance = mock_mongo_client.return_value
    mock_client_instance.__getitem__.return_value = "test_database"
    result = db_connection()
    assert result == "test_database"
    mock_mongo_client.assert_called_once_with(DATABASE_URI)


def test_db_connection_failure(app, mock_mongo_client):
    with app.app_context():
        error = ConnectionFailure("No se pudo conectar a la base de datos")
        mock_mongo_client.side_effect = error
        response, status_code = db_connection()
        assert response.json == {"err": f"Error de conexión a la base de datos: {error}"}
        assert status_code == 500
