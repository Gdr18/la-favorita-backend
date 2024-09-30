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
def extra_inputs_are_not_permitted(error) -> tuple[Response, int]:
    fields = []
    count = str(error).count('input_value=')
    find_start = 0
    while count > 0:
        index_input_value = str(error).find('input_value=', find_start)
        field = str(error)[index_input_value + 12:str(error).index("'", index_input_value + 13) + 1]
        fields.append(field)
        count -= 1
        find_start += index_input_value + 1

    response = jsonify(err=f"Error: {', '.join(fields)} {'no son campos válidos.' if len(fields) > 1 else 'no es un campo válido.'}")
    return response, 400


# Función para manejar errores de claves requeridas
def field_required(error, *args: str) -> tuple[Response, int]:
    qty_errors = str(error).count('Field required')
    str_args = ", ".join("'" + arg + "'" for arg in args)
    response = jsonify(err=f"{f'Faltan {qty_errors} campos requeridos' if int(qty_errors) > 1 else f'Falta {qty_errors} campo requerido'}. Los campos requeridos son: {str_args}.")
    return response, 400


# Función para manejar errores de tipos de datos
def input_should_be(error) -> tuple[Response, int]:
    fields = []
    count = str(error).count('Input should be a valid')
    find_start = str(error).find('Input should be a valid')
    while count > 0:
        index_field = str(error).rfind('\n', 0, find_start)
        field = str(error)[str(error).rfind('\n', 0, index_field - 2) + 1:index_field]
        index_type = str(error).find('valid ', find_start)
        type_field = str(error)[index_type + 6:str(error).find(" ", index_type + 6)]
        fields.append((field, type_field))
        count -= 1
        find_start += str(error).find('For', index_type)

    response = jsonify(
        err=' '.join(f"El campo '{field}' debe ser de tipo '{type_field}'." for field, type_field in fields)
    )
    return response, 400
