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


# TODO: Cambiar nombre a funciones
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
    qty_errors = str(error)[0]
    str_args = ", ".join("'" + arg + "'" for arg in args)
    response = jsonify(err=f"Error: {f'Faltan {qty_errors} campos requeridos' if int(qty_errors) > 1 else f'Falta {qty_errors} campo requerido'}. Los campos requeridos son: {str_args}.")
    return response, 400


# Función para manejar errores de tipos de datos
def input_should_be(error) -> tuple[Response, int]:
    # index_type = str(error).find('should be a valid')
    # type_field = str(error)[index_type + 18:str(error).find(" ", index_type + 18)]
    # index_field = str(error).find('Model')
    # field = str(error)[index_field + 6:str(error).find('\n', index_field + 6)]
    # response = jsonify(err=f"Error: El campo '{field}' debe ser de tipo '{type_field}'.")
    # return response, 400
    fields = []
    count = str(error).count('should be a valid')
    find_start = 0
    while count > 0:
        index_field = str(error).find('\n', find_start)
        field = str(error)[index_field + 1:str(error).find('\n', index_field + 1)]
        index_type = str(error).find('input_type=', find_start)
        type_field = str(error)[index_type + 11:str(error).find("]", index_type)]
        fields.append((field, type_field))
        count -= 1
        find_start += str(error).find('For', index_type)

    # response = jsonify(err=f"Error: {' '.join('El campo ' + field + ' debe ser de tipo '+ type_field + '.' for field, type_field in fields)}")
    response = jsonify(
        err=f"""Error: {' '.join(f"El campo '{field}' debe ser de tipo '{type_field}'." for field, type_field in fields)}"""
    )
    return response, 400
