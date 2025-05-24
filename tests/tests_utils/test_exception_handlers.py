import pytest
from pymongo.errors import PyMongoError, DuplicateKeyError, ConnectionFailure
from pydantic import ValidationError
from sendgrid import SendGridException

from src.utils.exception_handlers import (
    ValueCustomError,
    handle_custom_value_error,
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
    "function, arguments, code, error",
    [
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom1"],
            404,
            "not_found",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom2"],
            401,
            "password_not_match",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom3"],
            401,
            "email_not_confirmed",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom4"],
            429,
            "too_many_requests",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom5"],
            401,
            "not_auth",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom6"],
            401,
            "not_auth_set",
        ),
        (
            handle_extra_inputs_forbidden_error,
            EXTRA_INPUT_AND_FIELD_REQUIRED_ERRORS,
            400,
            "extra_input",
        ),
        (
            handle_field_required_error,
            EXTRA_INPUT_AND_FIELD_REQUIRED_ERRORS,
            400,
            "field_required",
        ),
        (
            handle_length_value_error,
            LENGTH_VALUE_ERRORS["too_short"],
            400,
            "length_value",
        ),
        (
            handle_length_value_error,
            LENGTH_VALUE_ERRORS["too_long"],
            400,
            "length_value",
        ),
        (
            handle_literal_value_error,
            LITERAL_VALUE_ERROR,
            400,
            "literal_value",
        ),
        (
            handle_pattern_value_error,
            PATTERN_ERROR,
            400,
            "pattern_value",
        ),
        (
            handle_custom_value_error,
            [{"msg": ", El ingrediente 'garbanzo' no existe"}],
            400,
            "custom_value",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type1"],
            400,
            "value_type",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type2"],
            400,
            "value_type",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type3"],
            400,
            "value_type",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type4"],
            400,
            "value_type",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["duplicate_key"],
            409,
            "db_duplicate_key",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["connection_failure"],
            500,
            "db_connection",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["generic_error"],
            500,
            "db_generic",
        ),
    ],
)
def test_exceptions_handlers(app, function, arguments, code, error):
    with app.app_context():
        err = (
            function(**arguments)
            if function == ValueCustomError
            else function(arguments)
        )

        response, status_code = err.response if function == ValueCustomError else err

        assert status_code == code
        assert response.json["err"] == error


def test_mongodb_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/mongodb-error")
        def trigger_mongodb_error():
            raise PyMongoError("Error de conexión")

        response = client.get("/mongodb-error")
        assert response.status_code == 500
        assert response.json["err"] == "db_generic"


def test_captured_validation_error_flask_handler(app):
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
        assert response.json["err"] == "pattern_value"


def test_non_captured_validation_error_flask_handler(app, mocker):
    with app.test_client() as client:
        fake_errors = [
            {"type": "bool_parsing", "msg": "Error desconocido", "loc": ["field"]},
            {"type": "bool_parsing", "msg": "Error desconocido", "loc": ["field"]},
        ]

        validation_error = ValidationError.from_exception_data(TokenModel, fake_errors)
        mocker.patch.object(validation_error, "errors", return_value=fake_errors)

        @app.route("/validation-error")
        def trigger_validation_error():
            raise validation_error

        response = client.get("/validation-error")

        assert response.status_code == 400
        assert response.json["err"] == "validation"


def test_value_custom_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/value-custom-error")
        def trigger_value_custom_error():
            raise ValueCustomError("not_found", "usuario")

        response = client.get("/value-custom-error")
        assert response.status_code == 404
        assert response.json["err"] == "not_found"


def test_sendgrid_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/sendgrid-error")
        def trigger_sendgrid_error():
            raise SendGridException("error")

        response = client.get("/sendgrid-error")
        assert response.status_code == 500
        assert response.json["err"] == "send_email"


def test_generic_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/generic-error")
        def trigger_generic_error():
            raise Exception("Error inesperado")

        response = client.get("/generic-error")
        assert response.status_code == 500
        assert response.json["err"] == "unexpected"
