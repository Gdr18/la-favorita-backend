import pytest
from flask import Response

from src.utils.json_responses import success_json_response, db_json_response


def test_resource_msg(app):
    with app.app_context():
        function = success_json_response("234525", "usuario", "añadido", 201)
        expected_msg = "Usuario '234525' ha sido añadido de forma satisfactoria"


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
