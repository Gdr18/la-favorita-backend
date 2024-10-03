from flask import jsonify, Response
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError
from bson import json_util

class ResourceNotFoundError(Exception):
    def __init__(self, user_id: int, resource: str):
        self.user_id = user_id
        self.resource = resource

    def json_response(self):
        return jsonify(err=f"El {self.resource} {self.user_id} no ha sido encontrado"), 404


# Función para manejar errores de campos no permitidos
def extra_inputs_are_not_permitted(errors: list) -> tuple[Response, int]:
    invalid_fields = [error["loc"][0] for error in errors if error["msg"] == "Extra inputs are not permitted"]
    formatting_invalid_fields = ', '.join(f"'{field}'" for field in invalid_fields)
    response = jsonify(err=f"""Hay {f"{len(invalid_fields)} campos que no son válidos" if len(invalid_fields) > 1 else f"{len(invalid_fields)} campo que no es válido"}: {formatting_invalid_fields}.""")
    return response, 400


# Función para manejar errores de campos requeridos
def field_required(errors: list) -> tuple[Response, int]:
    fields_required = [error["loc"][0] for error in errors if error["msg"] == "Field required"]
    formatting_fields_required = ', '.join([f"""'{error}'""" for error in fields_required])
    response = jsonify(err=f"{f'Faltan {len(fields_required)} campos requeridos ' if len(fields_required) > 1 else f'Falta {len(fields_required)} campo requerido'}: {formatting_fields_required}.")
    return response, 400


# Función para manejar errores de tipos de datos
def input_should_be(errors: list) -> tuple[Response, int]:
    fields = []
    for error in errors:
        field = error["loc"][0]
        first_index_type_field = error["msg"].find("valid") + 6
        last_index_type_field = error["msg"].find(" ", first_index_type_field)
        type_field = error["msg"][first_index_type_field:last_index_type_field if last_index_type_field != -1 else len(error["msg"])]
        fields.append((field, type_field))

    response = jsonify(
        err=' '.join(f"El campo '{field}' debe ser de tipo '{type_field[:-1] if ',' in type_field else type_field}'." for field, type_field in fields)
    )
    return response, 400


# Función para manejar errores de valores no permitidos
def value_error_formatting(errors: list) -> tuple[Response, int]:
    msg = [e["msg"][e["msg"].find(",") + 2:] for e in errors if e["msg"].startswith("Value error")]
    return jsonify({"err": " ".join(msg)}), 400


# Funciones para manejar excepciones
def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
    errors_list = error.errors()
    for e in errors_list:
        if e["msg"] == "Field required":
            return field_required(errors_list)
        if e["msg"].startswith("Input should be"):
            return input_should_be(errors_list)
        if e["msg"] == "Extra inputs are not permitted":
            return extra_inputs_are_not_permitted(errors_list)
        if e["msg"].startswith("value is not a valid email address"):
            return jsonify(err="El email no es válido."), 400
        if e["msg"].startswith("Value error"):
            return value_error_formatting(errors_list)
    return jsonify(err=[str(e) for e in errors_list]), 400


def handle_duplicate_key_error(error: DuplicateKeyError) -> tuple[Response, int]:
    return jsonify(err=f"Error de clave duplicada en MongoDB: {error.details['keyValue']}"), 409


def handle_unexpected_error(error: Exception) -> tuple[Response, int]:
    return jsonify(err=f"Ha ocurrido un error inesperado. {str(error)}"), 500
