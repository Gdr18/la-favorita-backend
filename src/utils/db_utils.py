from typing import Tuple

from pymongo import MongoClient
from pymongo.database import Database
from flask_bcrypt import Bcrypt
from flask import jsonify, Response

from config import database_uri


def db_connection() -> Database:
    try:
        client = MongoClient(database_uri)
        database = client["test_la_favorita"]
        return database
    except ConnectionError:
        print("No se pudo conectar a la base de datos")


# Instancias necesarias para la conexión a la base de datos y para el cifrado de contraseñas
db = db_connection()
bcrypt = Bcrypt()


# Función para comprobar el tipo de dato necesario para escribir en la base de datos
def type_checking(value, data_type, required: bool = False) -> bool:
    if (value == "" or value == [] or value == {} or value is None) and required is True:
        raise ValueError("ningún valor requerido puede estar vacío o ser nulo")
    if not required and value is None:
        return True
    if isinstance(value, data_type):
        return True
    else:
        raise TypeError(f"'{value}' debe ser un {data_type}")


# Función para manejar errores de claves no esperadas
def unexpected_keyword_argument(error: TypeError) -> tuple[Response, int]:
    key = str(error)[
        str(error).index("'") : str(error).index("'", str(error).index("'") + 1) + 1
    ]
    response = jsonify(err=f"Error: la clave {key} no es válida")
    print(response, 400)
    return response, 400


# Función para manejar errores de claves requeridas
def required_positional_argument(error: TypeError, *args: str) -> tuple[Response, int]:
    msg = str(error)[str(error).index(":") + 2 :].replace("and", "y")
    str_args = ", ".join("'" + arg + "'" for arg in args)
    response = jsonify(err=f"Error: Se ha olvidado {msg}. Son requeridos: {str_args}")
    print(response, 400)
    return response, 400

