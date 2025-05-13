import pytest
from pymongo.errors import PyMongoError, DuplicateKeyError, ConnectionFailure
from pydantic import ValidationError
from sendgrid import SendGridException

from src.utils.exception_handlers import (
    ValueCustomError,
    handle_model_custom_error,
    handle_field_required_error,
    handle_length_value_error,
    handle_extra_inputs_forbidden_error,
    handle_value_type_error,
    handle_literal_value_error,
    handle_pattern_value_error,
    handle_mongodb_exception,
)
from src.models.token_model import TokenModel
from tests.test_helpers import app

MONGODB_ERRORS = {
    "duplicate_key": DuplicateKeyError(
        "Duplicate key error", 11000, {"keyValue": "value"}
    ),
    "connection_failure": ConnectionFailure("Connection failed"),
    "generic_error": PyMongoError("Generic error"),
}
VALUE_CUSTOM_ERRORS = {
    "value_custom1": {"function": "not_found", "resource": "usuario"},
    "value_custom2": {"function": "not_match", "resource": None},
    "value_custom3": {"function": "not_confirmed", "resource": None},
    "value_custom4": {"function": "too_many_requests", "resource": None},
    "value_custom5": {"function": "not_authorized", "resource": None},
    "value_custom6": {"function": "not_authorized_to_set", "resource": "role"},
}
VALUE_TYPE_ERRORS = {
    "value_type1": [{"loc": ["field1"], "type": "int_"}],
    "value_type2": [{"loc": ["field1", 0], "type": "int_"}],
    "value_type3": [{"loc": ["field1", 0, "field2"], "type": "int_"}],
    "value_type4": [{"loc": ["field1", 0, "field2", 0, "field3"], "type": "int_"}],
}
LENGTH_VALUE_ERRORS = {
    "too_short": [{"loc": ["field1"], "type": "too_short", "ctx": {"min_length": 7}}],
    "too_long": [{"loc": ["field1"], "type": "too_long", "ctx": {"max_length": 5}}],
}
LITERAL_VALUE_ERROR = [
    {"loc": ["field1"], "ctx": {"expected": "main, starter or dessert"}}
]
EXTRA_INPUT_AND_FIELD_REQUIRED_ERRORS = [
    {"loc": ["field1"]},
    {"loc": ["field2"]},
]
PATTERN_ERROR = [{"loc": ["field1"]}]


@pytest.mark.parametrize(
    "function, arguments, code, message",
    [
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom1"],
            404,
            "Usuario no encontrado",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom2"],
            401,
            "La contraseña no coincide",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom3"],
            401,
            "El email no está confirmado",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom4"],
            429,
            "Se han reenviado demasiados emails de confirmación. Inténtalo mañana.",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom5"],
            401,
            "El token no está autorizado a acceder a esta ruta",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom6"],
            401,
            "El token no está autorizado a establecer 'role'",
        ),
        (
            handle_extra_inputs_forbidden_error,
            EXTRA_INPUT_AND_FIELD_REQUIRED_ERRORS,
            400,
            "Hay 2 campos que no son válidos: 'field1', 'field2'.",
        ),
        (
            handle_field_required_error,
            EXTRA_INPUT_AND_FIELD_REQUIRED_ERRORS,
            400,
            "Faltan 2 campos requeridos: 'field1', 'field2'.",
        ),
        (
            handle_length_value_error,
            LENGTH_VALUE_ERRORS["too_short"],
            400,
            "La longitud del campo 'field1' es demasiado corta. Debe tener al menos 7 caracteres.",
        ),
        (
            handle_length_value_error,
            LENGTH_VALUE_ERRORS["too_long"],
            400,
            "La longitud del campo 'field1' es demasiado larga. Debe tener como máximo 5 caracteres.",
        ),
        (
            handle_literal_value_error,
            LITERAL_VALUE_ERROR,
            400,
            "El campo 'field1' debe ser uno de los valores permitidos: main, starter o dessert.",
        ),
        (
            handle_pattern_value_error,
            PATTERN_ERROR,
            400,
            "El campo 'field1' no cumple con el patrón requerido.",
        ),
        (
            handle_model_custom_error,
            [{"msg": ", El ingrediente 'garbanzo' no existe"}],
            400,
            "El ingrediente 'garbanzo' no existe",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type1"],
            400,
            "El campo 'field1' debe ser de tipo 'int'.",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type2"],
            400,
            "El elemento anidado en 'field1' debe ser de tipo 'int'.",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type3"],
            400,
            "El campo 'field2' perteneciente a 'field1' debe ser de tipo 'int'.",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type4"],
            400,
            "El campo 'field3' anidado en 'field2' perteneciente a 'field1' debe ser de tipo 'int'.",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["duplicate_key"],
            409,
            "Error de clave duplicada en MongoDB: 'value'",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["connection_failure"],
            500,
            "Error de conexión con MongoDB: Connection failed",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["generic_error"],
            500,
            "Ha ocurrido un error en MongoDB: Generic error",
        ),
    ],
)
def test_exceptions_handlers(app, function, arguments, code, message):
    with app.app_context():
        error = (
            function(**arguments)
            if function == ValueCustomError
            else function(arguments)
        )

        response, status_code = (
            error.response if function == ValueCustomError else error
        )

        assert status_code == code
        assert response.json["err"] == message


def test_registration_mongodb_error(app):
    with app.test_client() as client:

        @app.route("/mongodb-error")
        def trigger_mongodb_error():
            raise PyMongoError("Error de conexión")

        response = client.get("/mongodb-error")
        assert response.status_code == 500
        assert "Error de conexión" in response.json["err"]


def test_registration_validation_error(app):
    with app.test_client() as client:

        @app.route("/validation-error")
        def trigger_validation_error():
            TokenModel(
                user_id="507f1f77bcf86cd79943901133",
                jti="bb53e637dd-8627-457c-840f-6cae52a12e8b",
                expires_at=1729684113900,
            )

        response = client.get("/validation-error")

        assert response.status_code == 400
        assert "no cumple con el patrón requerido" in response.json["err"]


def test_registration_value_custom_error(app):
    with app.test_client() as client:

        @app.route("/value-custom-error")
        def trigger_value_custom_error():
            raise ValueCustomError("not_found", "usuario")

        response = client.get("/value-custom-error")
        assert response.status_code == 404
        assert "Usuario no encontrado" in response.json["err"]


def test_registration_sendgrid_error(app):
    with app.test_client() as client:

        @app.route("/sendgrid-error")
        def trigger_sendgrid_error():
            raise SendGridException("error")

        response = client.get("/sendgrid-error")
        assert response.status_code == 500
        assert "Ha habido un error al enviar el correo" in response.json["err"]


def test_generic_error(app):
    with app.test_client() as client:

        @app.route("/generic-error")
        def trigger_generic_error():
            raise Exception("Error inesperado")

        response = client.get("/generic-error")
        assert response.status_code == 500
        assert "Ha ocurrido un error inesperado" in response.json["err"]
