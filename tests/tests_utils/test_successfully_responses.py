import pytest

from src.utils.successfully_responses import resource_deleted_msg, resource_added_msg, db_json_response
from tests.tests_tools import validate_success_response
from run import app as real_app


@pytest.fixture
def app():
    real_app.testing = True
    return real_app


status_code = 200


def test_resource_added_msg(app):
    with app.app_context():
        function = resource_added_msg("234525", "usuario")
        expected_msg = "El/la usuario con id '234525' ha sido añadido/a de forma satisfactoria"
        validate_success_response(function, status_code, expected_msg)


def test_resource_deleted_msg(app):
    with app.app_context():
        function = resource_deleted_msg("234525", "usuario")
        expected_msg = "El/la usuario con id '234525' ha sido eliminado/a de forma satisfactoria"
        validate_success_response(function, status_code, expected_msg)


def test_db_json_response():
    data = {
        "name": "John Doe",
        "email": "johndoe@doe.com",
        "password": "ValidPass!9",
        "role": 1,
    }

    response = db_json_response(data)
    assert response[1] == status_code
    assert isinstance(response[0], str)
