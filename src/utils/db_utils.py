from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask import jsonify, Response

from config import database


def db_connection():
    try:
        client = MongoClient(database)
        db = client["test_la_favorita"]
    except ConnectionError:
        print("No se pudo conectar a la base de datos")
    return db


# Instancias necesarias para la conexión a la base de datos y para el cifrado de contraseñas
db = db_connection()
bcrypt = Bcrypt()


# Función para comprobar el tipo de dato necesario para escribir en la base de datos
def type_checking(value, data_type) -> bool:
    if value:
        if isinstance(value, data_type):
            return True
        else:
            raise TypeError(f"'{value}' debe ser un {data_type}")
    else:
        raise ValueError("ningún valor requerido puede ser nulo o estar vacío")


# Función para manejar errores de claves no esperadas
def unexpected_keyword_argument(error: TypeError) -> Response:
    key = str(error)[
        str(error).index("'") : str(error).index("'", str(error).index("'") + 1) + 1
    ]
    return jsonify(err=f"Error: la clave {key} no es válida"), 400


# Función para manejar errores de claves requeridas
def required_positional_argument(error: TypeError, *args: str) -> Response:
    msg = str(error)[str(error).index(":") + 2 :].replace("and", "y")
    str_args = ", ".join("'" + arg + "'" for arg in args)
    return (
        jsonify(err=f"Error: Se ha olvidado {msg}. Son requeridos: {str_args}"),
        400,
    )
