import pytest
from flask import Response

from src.utils.successfully_responses import resource_msg, db_json_response
from tests.tests_tools import validate_success_response
from run import app as real_app


@pytest.fixture
def app():
    real_app.testing = True
    return real_app


def test_resource_msg(app):
    with app.app_context():
        function = resource_msg("234525", "usuario", "añadido", 201)
        expected_msg = "Usuario '234525' ha sido añadido de forma satisfactoria"
        validate_success_response(function, 201, expected_msg)


def test_db_json_response():
    data = {
        "name": "John Doe",
        "email": "johndoe@doe.com",
        "password": "ValidPass!9",
        "role": 1,
    }

    response = db_json_response(data)
    assert response[1] == 200
    assert isinstance(response[0], Response)
