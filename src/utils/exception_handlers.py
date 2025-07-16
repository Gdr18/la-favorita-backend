from flask import jsonify, Response, Flask
from pydantic import ValidationError
from sendgrid import SendGridException
from pymongo.errors import PyMongoError, DuplicateKeyError, ConnectionFailure
from bson.errors import InvalidId
from typing import Union


class ValueCustomError(Exception):
    def __init__(self, function: str, resource: str = None):
        self.function = function
        self.resource = resource

        if self.function == "not_authorized_to_set":
            self.response = self.json_response_not_authorized_to_set()
        elif self.function == "not_authorized":
            self.response = self.json_response_not_authorized()
        elif self.function == "not_found":
            self.response = self.json_response_not_found()
        elif self.function == "not_match":
            self.response = self.json_response_not_match()
        elif self.function == "not_confirmed":
            self.response = self.json_response_not_confirmed()
        elif self.function == "already_confirmed":
            self.response = self.json_response_already_confirmed()
        elif self.function == "too_many_requests":
            self.response = self.json_response_too_many_requests()
        elif self.function == "resource_required":
            self.response = self.json_response_resource_required()
        elif self.function == "bar_closed_manually":
            self.response = self.json_response_bar_closed_manually()
        elif self.function == "bar_closed_schedule":
            self.response = self.json_response_bar_closed_schedule()

    def json_response_not_found(self) -> tuple[Response, int]:
        return (
            jsonify(err="not_found", msg=f"{self.resource.capitalize()} no encontrado"),
            404,
        )

    @staticmethod
    def json_response_not_match() -> tuple[Response, int]:
        return jsonify(err="password_not_match", msg="La contraseña no coincide"), 401

    @staticmethod
    def json_response_not_confirmed() -> tuple[Response, int]:
        return (
            jsonify(err="email_not_confirmed", msg=f"El email no está confirmado"),
            401,
        )

    @staticmethod
    def json_response_already_confirmed() -> tuple[Response, int]:
        return (
            jsonify(err="email_already_confirmed", msg=f"El email ya está confirmado"),
            401,
        )

    @staticmethod
    def json_response_too_many_requests() -> tuple[Response, int]:
        return (
            jsonify(
                err="too_many_requests",
                msg=f"Se han reenviado demasiados emails de confirmación. Inténtalo más tarde.",
            ),
            429,
        )

    @staticmethod
    def json_response_not_authorized() -> tuple[Response, int]:
        return (
            jsonify(err="not_auth", msg=f"No está autorizado a acceder a este recurso"),
            403,
        )

    def json_response_not_authorized_to_set(self) -> tuple[Response, int]:
        return (
            jsonify(
                err="not_auth_set",
                msg=f"No está autorizado a establecer '{self.resource}'",
            ),
            403,
        )

    def json_response_resource_required(self):
        return (
            jsonify(
                err="resource_required",
                msg=f"'{self.resource.capitalize()}' requerido para esta operación",
            ),
            400,
        )

    @staticmethod
    def json_response_bar_closed_manually() -> tuple[Response, int]:
        return (
            jsonify(
                err="bar_closed_manually",
                msg="No se aceptan pedidos en este momento. Prueba dentro de un rato.",
            ),
            503,
        )

    @staticmethod
    def json_response_bar_closed_schedule() -> tuple[Response, int]:
        return (
            jsonify(
                err="bar_closed_schedule",
                msg="El bar está cerrado. Nuestro horario es: de 13:00 a 16:00 y de 20:00 a 0:00.",
            ),
            503,
        )


# Función para manejar errores de campos no permitidos
def handle_extra_inputs_forbidden_error(errors: list[dict]) -> tuple[Response, int]:
    formatting_invalid_fields = ", ".join(f"'{field['loc'][0]}'" for field in errors)
    response = jsonify(
        err="extra_input",
        msg=f"""Hay
{f"{len(errors)} campos que no son válidos" if len(errors) > 1 else f"{len(errors)} campo que no es válido"}: {formatting_invalid_fields}.""",
    )
    return response, 400


# Función para manejar errores de campos requeridos
def handle_field_required_error(errors: list[dict]) -> tuple[Response, int]:
    formatting_fields_required = ", ".join(
        [f"""'{error['loc'][0]}'""" for error in errors]
    )
    response = jsonify(
        err="field_required",
        msg=f"{f'Faltan {len(errors)} campos requeridos' if len(errors) > 1 else f'Falta 'f'{len(errors)} campo requerido'}: {formatting_fields_required}.",
    )
    return response, 400


# Función para manejar errores de tipos de datos
def handle_value_type_error(errors: list[dict]) -> tuple[Response, int]:
    response = []
    for error in errors:
        main_field = error["loc"][0]
        type_field = error["type"][: error["type"].find("_")]
        msg = ""
        if len(error["loc"]) == 1:
            msg = f"El campo '{main_field}' debe ser de tipo '{type_field}'."
        elif len(error["loc"]) == 2:
            msg = f"El elemento anidado en '{main_field}' debe ser de tipo '{type_field}'."
        elif len(error["loc"]) == 3:
            second_field = error["loc"][2]
            msg = f"El campo '{second_field}' perteneciente a '{main_field}' debe ser de tipo '{type_field}'."
        elif len(error["loc"]) == 5:
            second_field = error["loc"][2]
            third_field = error["loc"][4]
            msg = f"El campo '{third_field}' anidado en '{second_field}' perteneciente a '{main_field}' debe ser de tipo '{type_field}'."
        response.append(msg)
    return jsonify(err="value_type", msg=" ".join(response)), 400


# Función para manejar errores de valores literales
def handle_literal_value_error(errors: list[dict]) -> tuple[Response, int]:
    response = []
    for error in errors:
        main_field = error["loc"][0]
        expected_values = error["ctx"]["expected"].replace("or", "o")
        msg = f"El campo '{main_field}' debe ser uno de los valores permitidos: {expected_values}."
        response.append(msg)
    return jsonify(err="literal_value", msg=" ".join(response)), 400


# Función para manejar errores de valores no permitidos
def handle_custom_value_error(errors: list[dict]) -> tuple[Response, int]:
    msg = [error["msg"][error["msg"].find(",") + 2 :] for error in errors]
    return jsonify(err="custom_value", msg=" ".join(msg)), 400


# Función para manejar errores de longitud de campos
def handle_length_value_error(errors: list[dict]) -> tuple[Response, int]:
    fields = []
    for error in errors:
        response = ""
        if "too_short" in error["type"]:
            response = f"La longitud del campo '{error['loc'][0]}' es demasiado corta. Debe tener al menos {error['ctx']['min_length']} caracteres."
        elif "too_long" in error["type"]:
            response = f"La longitud del campo '{error['loc'][0]}' es demasiado larga. Debe tener como máximo {error['ctx']['max_length']} caracteres."
        fields.append(response)
    return jsonify(err="length_value", msg=" ".join(fields)), 400


# Función para manejar errores de patrón de campos
def handle_pattern_value_error(errors: list[dict]) -> tuple[Response, int]:
    fields = []
    for error in errors:
        field = error["loc"][0]
        fields.append(f"El campo '{field}' no cumple con el patrón requerido.")
    return jsonify(err="pattern_value", msg=" ".join(fields)), 400


# Función para manejar errores de MongoDB
def handle_mongodb_exception(
    error: Union[PyMongoError, InvalidId]
) -> tuple[Response, int]:
    if isinstance(error, DuplicateKeyError):
        return (
            jsonify(
                err="db_duplicate_key",
                msg=f"Error de clave duplicada en MongoDB: '{error.details['keyValue']}'",
            ),
            409,
        )
    elif isinstance(error, ConnectionFailure):
        return (
            jsonify(
                err="db_connection",
                msg=f"Error de conexión con MongoDB: {str(error)}",
            ),
            500,
        )
    elif isinstance(error, InvalidId):
        return (
            jsonify(
                err="db_invalid_id",
                msg=f"ID inválido proporcionado: Debe ser una entrada de 12 bytes o una cadena hexadecimal de 24 caracteres",
            ),
            400,
        )
    else:
        return (
            jsonify(
                err="db_generic",
                msg=f"Ha ocurrido un error en MongoDB: {str(error)}",
            ),
            500,
        )


# Función para registrar los gestores de excepciones globales
def register_global_exception_handlers(app: Flask) -> None:
    @app.errorhandler(PyMongoError)
    def handle_pymongo_error(error: PyMongoError) -> tuple[Response, int]:
        return handle_mongodb_exception(error)

    @app.errorhandler(InvalidId)
    def handle_pymongo_error(error: InvalidId) -> tuple[Response, int]:
        return handle_mongodb_exception(error)

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
        errors_list = error.errors()
        error_handlers = {
            "literal_error": handle_literal_value_error,
            "type": handle_value_type_error,
            "too_long": handle_length_value_error,
            "too_short": handle_length_value_error,
            "extra_forbidden": handle_extra_inputs_forbidden_error,
            "value_error": handle_custom_value_error,
            "missing": handle_field_required_error,
            "string_pattern_mismatch": handle_pattern_value_error,
        }

        for e in errors_list:
            for key, handler in error_handlers.items():
                if e["type"] == key or key in e["type"]:
                    relevant_errors = [
                        err
                        for err in errors_list
                        if err["type"] == key or key in err["type"]
                    ]
                    return handler(relevant_errors)

        return (
            jsonify(
                err="validation",
                msg=". ".join([f"Error: {str(e)}" for e in errors_list]),
            ),
            400,
        )

    @app.errorhandler(ValueCustomError)
    def handle_custom_error(error: ValueCustomError) -> tuple[Response, int]:
        return error.response

    @app.errorhandler(SendGridException)
    def handle_send_email_error(error: SendGridException) -> tuple[Response, int]:
        return jsonify(
            err="send_email",
            msg=f"Ha habido un error al enviar el correo de confirmación: {str(error)}",
        ), (error.status_code if hasattr(error, "status_code") else 500)

    @app.errorhandler(404)
    def handle_not_found_error(error: Exception) -> tuple[Response, int]:
        raise ValueCustomError("not_found", "recurso")

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> tuple[Response, int]:
        return (
            jsonify(
                err="unexpected",
                msg=f"Ha ocurrido un error inesperado: {str(error)}",
            ),
            500,
        )
