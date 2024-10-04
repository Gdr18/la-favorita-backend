import pytest

from run import app as real_app


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
