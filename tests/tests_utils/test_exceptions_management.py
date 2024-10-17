import pytest
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from src.models.user_model import UserModel
from src.models.product_model import ProductModel
from src.utils.exceptions_management import ClientCustomError, handle_validation_error, handle_duplicate_key_error, handle_unexpected_error
from tests.tests_tools import validate_error_response
from run import app as real_app


code_validation_error = 400


@pytest.fixture
def app():
    real_app.testing = True
    return real_app


def test_resource_not_found(app):
    with app.app_context():
        function = ClientCustomError("usuario", '1').json_response_not_found()
        expected_error_message = "El/la usuario '1' no ha sido encontrado/a."
        validate_error_response(function, 404, expected_error_message)


# tests para manejar errores de campos no permitidos
def test_handle_validation_error_extra_inputs_are_not_permitted(app):
    with app.app_context():
        try:
            UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass!9", role=1, color="red", size="big")
        except ValidationError as error:
            function = handle_validation_error(error)
            expected_error_message = "Hay 2 campos que no son válidos: 'color', 'size'."
            validate_error_response(function, code_validation_error, expected_error_message)


# Test para manejar errores de campos requeridos faltantes
def test_handle_validation_error_field_required(app):
    with app.app_context():
        try:
            UserModel()
        except ValidationError as error:
            function = handle_validation_error(error)
            expected_error_msg = "Faltan 3 campos requeridos: 'name', 'email', 'password'."
            validate_error_response(function, code_validation_error, expected_error_msg)


# Test para manejar errores de tipos de datos incorrectos
def test_handle_validation_error_input_should_be(app):
    with app.app_context():
        try:
            UserModel(name=234235, email="john.doe@example.com", password="ValidPass!9", role=1, phone=23252)
        except ValidationError as error:
            function = handle_validation_error(error)
            expected_error_message = "El campo 'name' debe ser de tipo 'string'. El campo 'phone' debe ser de tipo 'string'."
            validate_error_response(function, code_validation_error, expected_error_message)


# Test para manejar errores value error que necesitan formatearse
def test_handle_validation_error_value_error_formatting(app):
    with app.app_context():
        try:
            UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass", role=1)
        except ValidationError as error:
            function = handle_validation_error(error)
            expected_error_message = "La contraseña debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial (!@#$%^&*_-)"
            validate_error_response(function, code_validation_error, expected_error_message)


# Test para manejar errores de listas con menos elementos de los requeridos
def test_handle_validation_error_items_should_be_in_collection(app):
    with app.app_context():
        try:
            ProductModel(name="Tomato", stock=44, categories=[])
        except ValidationError as error:
            function = handle_validation_error(error)
            expected_error_message = "El campo 'categories' debe ser de tipo 'list' con al menos 1 elemento."
            validate_error_response(function, code_validation_error, expected_error_message)


# Test para manejar errores en el campo email
def test_handle_validation_error_invalid_email(app):
    with app.app_context():
        try:
            UserModel(name="John Dale", email="john.doe@example", password="ValidPass!9", role=1)
        except ValidationError as error:
            function = handle_validation_error(error)
            expected_error_message = "El email no es válido."
            validate_error_response(function, code_validation_error, expected_error_message)


# Test para manejar errores de validación inesperados
def test_handle_validation_error_default_case(app, mocker):
    with app.app_context():
        error_mock = mocker.Mock(spec=ValidationError)
        error_mock.errors.return_value = [
            {"msg": "Some other error"}
        ]
        function = handle_validation_error(error_mock)
        expected_error_message = ["{'msg': 'Some other error'}"]
        validate_error_response(function, code_validation_error, expected_error_message)


# Test para manejar errores de campos con valores duplicados
def test_handle_duplicate_key_error(app, mocker):
    with app.app_context():
        error = DuplicateKeyError("E11000 duplicate key error collection: db.collection index: _id_ dup key: { _id: 1 }")
        mocker.patch('pymongo.errors.DuplicateKeyError.details', new_callable=mocker.PropertyMock, return_value={"keyValue": {"_id": "1"}})

        function = handle_duplicate_key_error(error)
        expected_error_message = "Error de clave duplicada en MongoDB: {'_id': '1'}"
        validate_error_response(function, 409, expected_error_message)


# Test para manejar errores inesperados
def test_handle_unexpected_error(app):
    with app.app_context():
        error_message = "Test error"
        function = handle_unexpected_error(Exception(error_message))
        expected_error_message = f"Ha ocurrido un error inesperado. {error_message}"
        validate_error_response(function, 500, expected_error_message)
