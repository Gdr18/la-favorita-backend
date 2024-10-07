import pytest
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from src.models.user_model import UserModel
from src.models.product_model import ProductModel
from src.utils.exceptions_management import ResourceNotFoundError, handle_validation_error, handle_duplicate_key_error, handle_unexpected_error
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
        assert response.get_json()["err"] == "El usuario con id 1 no ha sido encontrado"


# tests para manejar errores de campos no permitidos
def test_handle_validation_error_extra_inputs_are_not_permitted(app):
    with app.app_context():
        try:
            UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass!9", role=1, color="red", size="big")
        except ValidationError as error:
            response, status_code = handle_validation_error(error)
            assert status_code == 400
            assert response.get_json()['err'] == "Hay 2 campos que no son válidos: 'color', 'size'."


# Test para manejar errores de campos requeridos faltantes
def test_handle_validation_error_field_required(app):
    with app.app_context():
        try:
            UserModel()
        except ValidationError as error:
            response, status_code = handle_validation_error(error)
            assert status_code == 400
            assert response.get_json()['err'] == "Faltan 3 campos requeridos: 'name', 'email', 'password'."


# Test para manejar errores de tipos de datos incorrectos
def test_handle_validation_error_input_should_be(app):
    with app.app_context():
        try:
            UserModel(name=234235, email="john.doe@example.com", password="ValidPass!9", role=1, phone=23252)
        except ValidationError as error:
            response, status_code = handle_validation_error(error)
            assert status_code == 400
            assert response.get_json()['err'] == "El campo 'name' debe ser de tipo 'string'. El campo 'phone' debe ser de tipo 'string'."


# Test para manejar errores value error que necesitan formatearse
def test_handle_validation_error_value_error_formatting(app):
    with app.app_context():
        try:
            UserModel(name="John Doe", email="john.doe@example.com", password="ValidPass", role=1)
        except ValidationError as error:
            response, status_code = handle_validation_error(error)
            assert status_code == 400
            assert response.get_json()['err'] == "La contraseña debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial (!@#$%^&*_-)"


# Test para manejar errorres de listas con menos elementos de los requeridos
def test_handle_validation_error_items_should_be_in_collection(app):
    with app.app_context():
        try:
            ProductModel(name="Tomato", stock=44, categories=[])
        except ValidationError as error:
            response, status_code = handle_validation_error(error)
            assert status_code == 400
            assert response.get_json()['err'] == "El campo 'categories' debe ser de tipo 'list' con al menos 1 elemento."


# Test para manejar errores en el campo email
def test_handle_validation_error_invalid_email(app):
    with app.app_context():
        try:
            UserModel(name="John Dale", email="john.doe@example", password="ValidPass!9", role=1)
        except ValidationError as error:
            response, status_code = handle_validation_error(error)
            assert status_code == 400
            assert response.get_json()['err'] == "El email no es válido."


# Test para manejar errores de validación inesperados
def test_handle_validation_error_default_case(app, mocker):
    with app.app_context():
        error_mock = mocker.Mock(spec=ValidationError)
        error_mock.errors.return_value = [
            {"msg": "Some other error"}
        ]
        response, status_code = handle_validation_error(error_mock)
        assert status_code == 400
        assert response.get_json()["err"] == ["{'msg': 'Some other error'}"]


# Test para manejar errores de campos con valores duplicados
def test_handle_duplicate_key_error(app, mocker):
    with app.app_context():
        error = DuplicateKeyError("E11000 duplicate key error collection: db.collection index: _id_ dup key: { _id: 1 }")
        mocker.patch('pymongo.errors.DuplicateKeyError.details', new_callable=mocker.PropertyMock, return_value={"keyValue": {"_id": "1"}})

        response, status_code = handle_duplicate_key_error(error)

        assert status_code == 409
        assert response.get_json() == {"err": "Error de clave duplicada en MongoDB: {'_id': '1'}"}


# Test para manejar errores inesperados
def test_handle_unexpected_error(app):
    with app.app_context():
        error_message = "Test error"
        response, status_code = handle_unexpected_error(Exception(error_message))

        assert status_code == 500
        assert response.get_json() == {"err": f"Ha ocurrido un error inesperado. {error_message}"}
