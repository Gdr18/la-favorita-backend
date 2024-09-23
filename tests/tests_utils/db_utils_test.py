import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure
from flask import Flask

from src.utils.db_utils import db_connection, type_checking, unexpected_keyword_argument, required_positional_argument
from config import database_uri

# Tests db_connection


@patch("src.utils.db_utils.MongoClient")
def test_db_connection_success(mock_mongo_client):
    # Configurar el mock para que devuelva un cliente de base de datos simulado
    mock_client_instance = MagicMock()
    mock_mongo_client.return_value = mock_client_instance
    mock_client_instance.__getitem__.return_value = "test_database"

    # Llamar a la función y verificar el resultado
    result = db_connection()
    assert result == "test_database"
    mock_mongo_client.assert_called_once_with(database_uri)


@patch("src.utils.db_utils.MongoClient")
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

# Tests type_checking


def test_type_checking_valid():
    assert type_checking(123, int) is True
    assert type_checking("test", str) is True
    assert type_checking([1, 2, 3], list) is True
    assert type_checking(None, None) is True


def test_type_checking_required():
    with pytest.raises(ValueError):
        type_checking("", str, required=True)
    with pytest.raises(ValueError):
        type_checking([], list, required=True)
    with pytest.raises(ValueError):
        type_checking({}, dict, required=True)
    with pytest.raises(ValueError):
        type_checking(None, int, required=True)


def test_type_checking_invalid_type():
    with pytest.raises(TypeError):
        type_checking(123, str)
    with pytest.raises(TypeError):
        type_checking("test", int)
    with pytest.raises(TypeError):
        type_checking([1, 2, 3], dict)
    with pytest.raises(TypeError):
        type_checking(2, float)


# test unexpected_keyword_argument


@pytest.fixture
def app():
    app = Flask(__name__)
    app.testing = True
    return app


def test_unexpected_keyword_argument(app):
    with app.app_context():
        error = TypeError("unexpected keyword argument 'invalid_key'")
        response, status_code = unexpected_keyword_argument(error)
        assert status_code == 400
        assert "Error: la clave 'invalid_key' no es valida".encode() in response.data


# tests required_positional_argument


def test_required_positional_argument(app):
    with app.app_context():
        error = TypeError("missing 1 required positional argument: 'arg1'")
        response, status_code = required_positional_argument(error, "arg1")
        assert status_code == 400
        assert "Error: Se ha olvidado 'arg1'. Son requeridos: 'arg1'".encode() in response.data


def test_required_positional_argument_multiple_args(app):
    with app.app_context():
        error = TypeError("missing 3 required positional arguments: 'arg1', 'arg2' and 'arg3'")
        response, status_code = required_positional_argument(error, "arg1", "arg2", "arg3")
        assert status_code == 400
        assert "Error: Se ha olvidado 'arg1', 'arg2' y 'arg3'. Son requeridos: 'arg1', 'arg2', 'arg3".encode() in response.data
