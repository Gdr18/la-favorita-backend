from flask import jsonify, Response
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError
from sendgrid import SendGridException


class ClientCustomError(Exception):
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
        elif self.function == "too_many_requests":
            self.response = self.json_response_too_many_requests()

    def json_response_not_found(self) -> tuple[Response, int]:
        return jsonify(err=f"{self.resource.capitalize()} no encontrado"), 404

    @staticmethod
    def json_response_not_match() -> tuple[Response, int]:
        return jsonify(err="La contraseña no coincide"), 401

    @staticmethod
    def json_response_not_confirmed() -> tuple[Response, int]:
        return jsonify(err=f"El email no está confirmado"), 401

    @staticmethod
    def json_response_too_many_requests() -> tuple[Response, int]:
        return jsonify(err=f"Se han reenviado demasiados emails de confirmación. Inténtalo mañana."), 429

    @staticmethod
    def json_response_not_authorized() -> tuple[Response, int]:
        return jsonify(err=f"El token no está autorizado a acceder a esta ruta"), 401

    def json_response_not_authorized_to_set(self) -> tuple[Response, int]:
        return jsonify(err=f"El token no está autorizado a establecer '{self.resource}'"), 401


# Función para manejar errores de campos no permitidos
def handle_extra_inputs_forbidden_error(errors: list[dict]) -> tuple[Response, int]:
    formatting_invalid_fields = ", ".join(f"'{field['loc'][0]}'" for field in errors)
    response = jsonify(
        err=f"""Hay {f"{len(errors)} campos que no son válidos" if len(errors) > 1 else f"{len(errors)} campo que no es válido"}: {formatting_invalid_fields}."""
    )
    return response, 400


# Función para manejar errores de campos requeridos
def handle_field_required_error(errors: list[dict]) -> tuple[Response, int]:
    formatting_fields_required = ", ".join([f"""'{error['loc'][0]}'""" for error in errors])
    response = jsonify(
        err=f"{f'Faltan {len(errors)} campos requeridos' if len(errors) > 1 else f'Falta {len(errors)} campo requerido'}: {formatting_fields_required}."
    )
    return response, 400


# Función para manejar errores de tipos de datos
# TODO: Cambiar para capturar los errores de tipos de datos subyacentes en listas y diccionarios.
def handle_value_type_error(errors: list[dict]) -> tuple[Response, int]:
    fields = []
    for error in errors:
        main_field = error["loc"][0]
        type_field = error["type"][: error["type"].find("_")]
        msg = ""
        # TODO: Hacer función propia
        if type_field == "literal":
            expected_values = error["ctx"]["expected"].replace("or", "o")
            msg = f"El campo '{main_field}' debe ser uno de los valores permitidos: {expected_values}."
        elif len(error["loc"]) == 1:
            msg = f"El campo '{main_field}' debe ser de tipo '{type_field}'."
        elif len(error["loc"]) == 2 and error["loc"][1] == 0:
            msg = f"El elemento del interior de la colección de '{main_field}' debe ser de tipo '{type_field}'."
        elif len(error["loc"]) == 3:
            second_field = error["loc"][2]
            msg = f"El campo '{second_field}' perteneciente a '{main_field}' debe ser de tipo '{type_field}'."
        elif len(error["loc"]) == 5:
            second_field = error["loc"][2]
            third_field = error["loc"][4]
            msg = f"El campo '{third_field}' anidado en '{second_field}' perteneciente a '{main_field}' debe ser de tipo '{type_field}'."
        fields.append(msg)
    return jsonify(err=" ".join(fields)), 400


# Función para manejar errores de valores no permitidos
def handle_custom_value_error(errors: list[dict]) -> tuple[Response, int]:
    msg = [error["msg"][error["msg"].find(",") + 2 :] for error in errors]
    return jsonify({"err": " ".join(msg)}), 400


# Función para manejar errores de longitud de campos
def handle_length_value_error(errors: list[dict]) -> tuple[Response, int]:
    fields = []
    for error in errors:
        response = ""
        if "too_short" in error["type"]:
            response = f"La longitud del campo '{error['loc'][0]}' es demasiado corta. Debe tener al menos {error['ctx']['min_length']}."
        elif "too_long" in error["type"]:
            response = f"La longitud del campo '{error['loc'][0]}' es demasiado larga. Debe tener como máximo {error['ctx']['max_length']}."
        fields.append(response)
    return jsonify(err=" ".join(fields)), 400


# Función para manejar errores de patrón de campos
def handle_pattern_value_error(errors: list[dict]) -> tuple[Response, int]:
    fields = []
    for error in errors:
        field = error["loc"][0]
        fields.append(f"El campo '{field}' no cumple con el patrón requerido.")
    return jsonify(err=" ".join(fields)), 400


# Funciones para manejar excepciones
# def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
#     errors_list = error.errors()
#     for e in errors_list:
#         if "type" in e["type"] or e["type"] == "literal_error":
#             value_type_errors = [error for error in errors_list if error["msg"].startswith("Input should be")]
#             return handle_value_type_error(value_type_errors)
#         if "too_long" in e["type"] or "too_short" in e["type"]:
#             length_value_errors = [
#                 error for error in errors_list if "too_long" in error["type"] or "too_short" in error["type"]
#             ]
#             return handle_length_value_error(length_value_errors)
#         if e["type"] == "extra_forbidden":
#             extra_fields_errors = [error for error in errors_list if error["type"] == "extra_forbidden"]
#             return handle_extra_inputs_forbidden_error(extra_fields_errors)
#         if e["type"] == "value_error":
#             custom_value_error_errors = [error for error in errors_list if error["type"] == "value_error"]
#             return handle_custom_value_error(custom_value_error_errors)
#         if e["type"] == "missing":
#             field_required_errors = [error for error in errors_list if error["type"] == "missing"]
#             return handle_field_required_error(field_required_errors)
#         if e["type"] == "string_pattern_mismatch":
#             pattern_errors = [error for error in errors_list if error["type"] == "string_pattern_mismatch"]
#             return handle_pattern_field_error(pattern_errors)
#     return jsonify(err=[str(e) for e in errors_list]), 400


# TODO: Probar la siguiente función
def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
    errors_list = error.errors()
    error_handlers = {
        "literal_error": handle_value_type_error,
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
                relevant_errors = [err for err in errors_list if err["type"] == key or key in err["type"]]
                return handler(relevant_errors)

    return jsonify(err=[str(e) for e in errors_list]), 400


def handle_send_email_error(error: SendGridException) -> tuple[Response, int]:
    return jsonify(err=f"Ha habido un error al enviar el correo de confirmación: {error}"), (
        error.status_code if hasattr(error, "status_code") else 500
    )


def handle_duplicate_key_error(error: DuplicateKeyError) -> tuple[Response, int]:
    return jsonify(err=f"Error de clave duplicada en MongoDB: {error.details['keyValue']}"), 409


def handle_unexpected_error(error: Exception) -> tuple[Response, int]:
    return jsonify(err=f"Ha ocurrido un error inesperado. {str(error)}"), 500
