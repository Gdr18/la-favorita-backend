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
