import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure
from flask import Flask

from src.utils.db_utils import db_connection, extra_inputs_are_not_permitted, field_required, input_should_be
from config import database_uri
from run import app as real_app


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


@pytest.fixture
def app():
    real_app.testing = True
    return app


# tests extra_inputs_are_not_permitted
def test_single_invalid_field(app):
    with real_app.app_context():
        error_message = "input_value='invalid_field'"
        response, status_code = extra_inputs_are_not_permitted(error_message)
        assert status_code == 400
        assert "'invalid_field' no es un campo válido." in response.get_json()["err"]


def test_multiple_invalid_fields(app):
    with real_app.app_context():
        error_message = "input_value='field1' input_value='field2'"
        response, status_code = extra_inputs_are_not_permitted(error_message)
        assert status_code == 400
        assert "'field1', 'field2' no son campos válidos." in response.get_json()["err"]


# tests field_required
def test_single_required_field(app):
    with real_app.app_context():
        error_message = "Field required"
        response, status_code = field_required(error_message, "field1")
        assert status_code == 400
        assert "Falta 1 campo requerido. Los campos requeridos son: 'field1'." in response.get_json()["err"]


def test_multiple_required_fields(app):
    with real_app.app_context():
        error_message = "Field required Field required"
        response, status_code = field_required(error_message, "field1", "field2")
        assert status_code == 400
        assert "Faltan 2 campos requeridos. Los campos requeridos son: 'field1', 'field2'." in response.get_json()["err"]


# test_input_should_be
def test_single_invalid_type(app):
    with real_app.app_context():
        error_message = "validation errors for UserModel\nfield_name\n  Input should be a valid string [type=string_type, input_value=2352235, input_type=int]\n"
        response, status_code = input_should_be(error_message)
        assert status_code == 400
        assert "El campo 'field_name' debe ser de tipo 'string'." in response.get_json()["err"]


def test_multiple_invalid_type(app):
    with real_app.app_context():
        error_message = "validation errors for UserModel\nfield_name\n  Input should be a valid string [type=string_type, input_value=2352235, input_type=str]\n For further information visit \nanother_field\n  Input should be a valid list [type=list_type, input_value={}, input_type=int]\n For"
        response, status_code = input_should_be(error_message)
        assert status_code == 400
        assert "El campo 'field_name' debe ser de tipo 'string'. El campo 'another_field' debe ser de tipo 'list'" in response.get_json()["err"]
