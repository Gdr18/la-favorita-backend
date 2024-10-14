from flask import jsonify, Response
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError


class ResourceNotFoundError(Exception):
    def __init__(self, user_id: str, resource: str):
        self.user_id = user_id
        self.resource = resource

    def json_response(self) -> tuple[Response, int]:
        return jsonify(err=f"El/la {self.resource} con id '{self.user_id}' no ha sido encontrado/a."), 404


# Función para manejar errores de campos no permitidos
def extra_inputs_are_not_permitted(errors: list) -> tuple[Response, int]:
    formatting_invalid_fields = ', '.join(f"'{field['loc'][0]}'" for field in errors)
    response = jsonify(err=f"""Hay {f"{len(errors)} campos que no son válidos" if len(errors) > 1 else f"{len(errors)} campo que no es válido"}: {formatting_invalid_fields}.""")
    return response, 400


# Función para manejar errores de campos requeridos
def field_required(errors: list) -> tuple[Response, int]:
    formatting_fields_required = ', '.join([f"""'{error['loc'][0]}'""" for error in errors])
    response = jsonify(err=f"{f'Faltan {len(errors)} campos requeridos' if len(errors) > 1 else f'Falta {len(errors)} campo requerido'}: {formatting_fields_required}.")
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
    msg = [error["msg"][error["msg"].find(",") + 2:] for error in errors]
    return jsonify({"err": " ".join(msg)}), 400


def items_should_be_in_collection(errors: list) -> tuple[Response, int]:
    source_selected = []
    for error in errors:
        field = error["loc"][0]
        type_field = error["msg"][:error["msg"].find(" ")]
        first_index_items_number = error["msg"].find("at least ") + 9
        last_index_items_number = error["msg"].find(" ", first_index_items_number)
        items_number = error["msg"][first_index_items_number:last_index_items_number]
        source_selected.append((field, type_field, items_number))
    msg = [f"El campo '{field}' debe ser de tipo '{type_field.lower()}' con al menos {items_number} elemento." for field, type_field, items_number in source_selected]
    return jsonify({"err": " ".join(msg)}), 400


# Funciones para manejar excepciones
def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
    errors_list = error.errors()
    for e in errors_list:
        if e["msg"].startswith("Input should be"):
            errors_input_should_be = [error for error in errors_list if error["msg"].startswith("Input should be")]
            return input_should_be(errors_input_should_be)
        if e["msg"] == "Extra inputs are not permitted":
            errors_extra_inputs_are_not_permitted = [error for error in errors_list if error["msg"] == "Extra inputs are not permitted"]
            return extra_inputs_are_not_permitted(errors_extra_inputs_are_not_permitted)
        if e["msg"].startswith("Value error"):
            errors_value_error = [error for error in errors_list if error["msg"].startswith("Value error")]
            return value_error_formatting(errors_value_error)
        if e["msg"].startswith("List should have at least"):
            errors_should_be_in_list = [error for error in errors_list if error["msg"].startswith("List should have at least")]
            return items_should_be_in_collection(errors_should_be_in_list)
        if e["msg"] == "Field required":
            errors_field_required = [error for error in errors_list if error["msg"] == "Field required"]
            return field_required(errors_field_required)
        if e["msg"].startswith("value is not a valid email address"):
            return jsonify(err="El email no es válido."), 400
    return jsonify(err=[str(e) for e in errors_list]), 400


def handle_duplicate_key_error(error: DuplicateKeyError) -> tuple[Response, int]:
    return jsonify(err=f"Error de clave duplicada en MongoDB: {error.details['keyValue']}"), 409


def handle_unexpected_error(error: Exception) -> tuple[Response, int]:
    return jsonify(err=f"Ha ocurrido un error inesperado. {str(error)}"), 500
