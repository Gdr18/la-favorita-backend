import pytest

from src.utils.exceptions_management import ResourceNotFoundError, extra_inputs_are_not_permitted, field_required, input_should_be, handle_unexpected_error, handle_validation_error, handle_duplicate_key_error
from run import app as real_app


@pytest.fixture
def app():
    real_app.testing = True
    return real_app


def test_resource_not_found(app):
    with app.app_context():
        error = ResourceNotFoundError(1, "usuario")
        response, status_code = error.json_response()
        assert status_code == 404
        assert "El usuario con id 1 no ha sido encontrado" in response.get_json()["err"]


# tests extra_inputs_are_not_permitted
def test_single_extra_inputs_are_not_permitted():
    with real_app.app_context():
        error_message = [{"loc": ["field_name"]}]
        response, status_code = extra_inputs_are_not_permitted(error_message)
        assert status_code == 400
        assert "Hay 1 campo que no es válido: 'field_name'." in response.get_json()["err"]


def test_multiple_extra_inputs_are_not_permitted(app):
    with real_app.app_context():
        error_message = [{"loc": ["field_name"]}, {"loc": ["field_name2"]}]
        response, status_code = extra_inputs_are_not_permitted(error_message)
        assert status_code == 400
        assert "Hay 2 campos que no son válidos: 'field_name', 'field_name2'." in response.get_json()["err"]


# tests field_required
def test_single_field_required(app):
    with real_app.app_context():
        error_message = [{"loc": ["field1"]}]
        response, status_code = field_required(error_message)
        assert status_code == 400
        assert "Falta 1 campo requerido: 'field1'." in response.get_json()["err"]


def test_multiple_field_required(app):
    with real_app.app_context():
        error_message = [{"loc": ["field1"]}, {"loc": ["field2"]}]
        response, status_code = field_required(error_message)
        assert status_code == 400
        assert "Faltan 2 campos requeridos: 'field1', 'field2'." in response.get_json()["err"]


# test_input_should_be
def test_single_input_should_be(app):
    with real_app.app_context():
        error_message = [{"loc": ["field_name"], "msg": "Input should be a valid string"}]
        response, status_code = input_should_be(error_message)
        assert status_code == 400
        assert "El campo 'field_name' debe ser de tipo 'string'." in response.get_json()["err"]


def test_multiple_invalid_type(app):
    with real_app.app_context():
        error_message = [{"loc": ["field_name"], "msg": "Input should be a valid string"}, {"loc": ["another_field"], "msg": "Input should be a valid list"}]
        response, status_code = input_should_be(error_message)
        assert status_code == 400
        assert "El campo 'field_name' debe ser de tipo 'string'. El campo 'another_field' debe ser de tipo 'list'" in response.get_json()["err"]
