import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure
from flask import Flask

from src.utils.db_utils import db_connection, extra_inputs_are_not_permitted, field_required
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


# test unexpected_keyword_argument
@pytest.fixture
def app():
    app = Flask(__name__)
    app.testing = True
    return app


def test_single_invalid_field(app):
    with app.app_context():
        error_message = "input_value='invalid_field'"
        response, status_code = extra_inputs_are_not_permitted(error_message)
        assert status_code == 400
        assert "'invalid_field' no es un campo válido." in response.get_json()["err"]


def test_multiple_invalid_fields(app):
    with app.app_context():
        error_message = "input_value='field1' input_value='field2'"
        response, status_code = extra_inputs_are_not_permitted(error_message)
        assert status_code == 400
        assert "'field1', 'field2' no son campos válidos." in response.get_json()["err"]


# tests field_required
def test_single_required_field(app):
    with app.app_context():
        error_message = "1"
        response, status_code = field_required(error_message, "field1")
        assert status_code == 400
        assert "Falta 1 campo requerido. Los campos requeridos son: 'field1'." in response.get_json()["err"]


def test_multiple_required_fields(app):
    with app.app_context():
        error_message = "2"
        response, status_code = field_required(error_message, "field1", "field2")
        assert status_code == 400
        assert "Faltan 2 campos requeridos. Los campos requeridos son: 'field1', 'field2'." in response.get_json()["err"]

