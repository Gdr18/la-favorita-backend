from pymongo.mongo_client import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from flask_bcrypt import Bcrypt
from flask import jsonify, Response

from config import database_uri


def db_connection() -> Database:
    try:
        client = MongoClient(database_uri)
        database = client["test_la_favorita"]
        return database
    except ConnectionFailure:
        print("No se pudo conectar a la base de datos")


# Instancias necesarias para la conexión a la base de datos y para el cifrado de contraseñas
db = db_connection()
bcrypt = Bcrypt()


# def get_allowed_values(collection_name):
#     collection = db[collection_name]
#     return [item["value"] for item in collection.find()]
#
#
# allowed_allergens = get_allowed_values("allergens")
# allowed_category = get_allowed_values("categories")
#
#
# def reload_allowed_values():
#     global allowed_allergens, allowed_category
#     allowed_allergens = get_allowed_values("allergens")
#     allowed_category = get_allowed_values("categories")


# Función para manejar errores de campos no permitidos
def extra_inputs_are_not_permitted(errors: list) -> tuple[Response, int]:
    invalid_fields = [error["loc"][0] for error in errors if error["msg"] == "Extra inputs are not permitted"]
    formatting_invalid_fields = ', '.join(f"'{field}'" for field in invalid_fields)
    response = jsonify(err=f"""Hay {f"{len(invalid_fields)} campos que no son válidos" if len(invalid_fields) > 1 else f"{len(invalid_fields)} campo que no es válido"}: {formatting_invalid_fields}.""")
    return response, 400


# Función para manejar errores de claves requeridas
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


def value_error_formatting(errors: list) -> tuple[Response, int]:
    msg = [error["msg"][error["msg"].find(",") + 2:] for error in errors]
    return jsonify({"err": " ".join(msg)}), 400
