from flask import jsonify, Response
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError


class ClientCustomError(Exception):
    def __init__(self, function: str, resource: str = None):
        self.function = function
        self.resource = resource

        if self.function == "not_authorized_to_set_role":
            self.response = self.json_response_not_authorized_to_set_role()
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

    @staticmethod
    def json_response_not_authorized_to_set_role() -> tuple[Response, int]:
        return jsonify(err=f"El token no está autorizado a establecer el rol"), 401


# Función para manejar errores de campos no permitidos
def extra_inputs_are_not_permitted(errors: list) -> tuple[Response, int]:
    formatting_invalid_fields = ", ".join(f"'{field['loc'][0]}'" for field in errors)
    response = jsonify(
        err=f"""Hay {f"{len(errors)} campos que no son válidos" if len(errors) > 1 else f"{len(errors)} campo que no es válido"}: {formatting_invalid_fields}."""
    )
    return response, 400


# Función para manejar errores de campos requeridos
def field_required(errors: list) -> tuple[Response, int]:
    formatting_fields_required = ", ".join([f"""'{error['loc'][0]}'""" for error in errors])
    response = jsonify(
        err=f"{f'Faltan {len(errors)} campos requeridos' if len(errors) > 1 else f'Falta {len(errors)} campo requerido'}: {formatting_fields_required}."
    )
    return response, 400


# Función para manejar errores de tipos de datos
def field_type(errors: list) -> tuple[Response, int]:
    fields = []
    for error in errors:
        field = error["loc"][0]
        first_index_type_field = error["msg"].find("valid") + 6
        last_index_type_field = error["msg"].find(" ", first_index_type_field)
        type_field = error["msg"][
            first_index_type_field : (last_index_type_field if last_index_type_field != -1 else len(error["msg"]))
        ]
        fields.append((field, type_field))

    response = jsonify(
        err=" ".join(
            f"El campo '{field}' debe ser de tipo '{type_field[:-1] if ',' in type_field else type_field}'."
            for field, type_field in fields
        )
    )
    return response, 400


# Función para manejar errores de valores no permitidos
def value_error_formatting(errors: list) -> tuple[Response, int]:
    msg = [error["msg"][error["msg"].find(",") + 2 :] for error in errors]
    return jsonify({"err": " ".join(msg)}), 400


# Función para manejar errores de longitud de campos
def field_length(errors: list) -> tuple[Response, int]:
    fields = []
    for error in errors:
        if "too_short" in error["type"]:
            too_short = f"La longitud del campo '{error['loc'][0]}' es demasiado corta. Debe tener al menos {error['ctx']['min_length']}."
            fields.append(too_short)
        elif "too_long" in error["type"]:
            too_long = f"La longitud del campo '{error['loc'][0]}' es demasiado larga. Debe tener como máximo {error['ctx']['max_length']}."
            fields.append(too_long)
    return jsonify(err=" ".join(fields)), 400


# Funciones para manejar excepciones
def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
    errors_list = error.errors()
    for e in errors_list:
        if e["msg"].startswith("Input should be"):
            errors_input_should_be = [error for error in errors_list if error["msg"].startswith("Input should be")]
            return field_type(errors_input_should_be)
        if "too_long" in e["type"] or "too_short" in e["type"]:
            errors_string_length = [
                error for error in errors_list if "too_long" in error["type"] or "too_short" in error["type"]
            ]
            return field_length(errors_string_length)
        if e["msg"] == "Extra inputs are not permitted":
            errors_extra_inputs_are_not_permitted = [
                error for error in errors_list if error["msg"] == "Extra inputs are not permitted"
            ]
            return extra_inputs_are_not_permitted(errors_extra_inputs_are_not_permitted)
        if e["msg"].startswith("Value error"):
            errors_value_error = [error for error in errors_list if error["msg"].startswith("Value error")]
            return value_error_formatting(errors_value_error)
        if e["msg"] == "Field required":
            errors_field_required = [error for error in errors_list if error["msg"] == "Field required"]
            return field_required(errors_field_required)
    return jsonify(err=[str(e) for e in errors_list]), 400


# TODO: Probar la siguiente función
# def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
#     errors_list = error.errors()
#     error_handlers = {
#         "Input should be": field_type,
#         "too_long": field_length,
#         "too_short": field_length,
#         "Extra inputs are not permitted": extra_inputs_are_not_permitted,
#         "Value error": value_error_formatting,
#         "Field required": field_required,
#     }
#
#     for e in errors_list:
#         for key, handler in error_handlers.items():
#             if e["msg"].startswith(key) or key in e["type"]:
#                 relevant_errors = [err for err in errors_list if err["msg"].startswith(key) or key in err["type"]]
#                 return handler(relevant_errors)
#
#     return jsonify(err=[str(e) for e in errors_list]), 400


def handle_duplicate_key_error(error: DuplicateKeyError) -> tuple[Response, int]:
    return jsonify(err=f"Error de clave duplicada en MongoDB: {error.details['keyValue']}"), 409


def handle_unexpected_error(error: Exception) -> tuple[Response, int]:
    return jsonify(err=f"Ha ocurrido un error inesperado. {str(error)}"), 500
