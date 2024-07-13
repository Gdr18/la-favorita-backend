from pymongo import MongoClient
from flask_bcrypt import Bcrypt

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


def type_checking(value, type: str) -> bool:
    if value:
        if isinstance(value, type):
            return True
        else:
            raise TypeError(f"'{value}' debe ser un {type}")
    else:
        raise ValueError("ningún valor requerido puede ser nulo o estar vacío")
