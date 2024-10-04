import pytest
from pymongo.errors import ConnectionFailure

from src.utils.db_utils import db_connection
from config import database_uri


# Tests db_connection
@pytest.fixture
def mock_mongo_client(mocker):
    return mocker.patch("src.utils.db_utils.MongoClient")


def test_db_connection_success(mock_mongo_client):
    # Configurar el mock para que devuelva un cliente de base de datos simulado
    mock_client_instance = mock_mongo_client.return_value
    mock_client_instance.__getitem__.return_value = "test_database"

    # Llamar a la función y verificar el resultado
    result = db_connection()
    assert result == "test_database"
    mock_mongo_client.assert_called_once_with(database_uri)


def test_db_connection_failure(mock_mongo_client, capsys):
    # Configurar el mock para que lance una excepción de fallo de conexión
    mock_mongo_client.side_effect = ConnectionFailure("No se pudo conectar a la base de datos")

    # Llamar a la función y verificar que maneja la excepción correctamente
    db = db_connection()

    # Captura la salida de la consola
    captured = capsys.readouterr()

    # Verifica que el mensaje de error se haya impreso
    assert "No se pudo conectar a la base de datos" in captured.out
    assert db is None
