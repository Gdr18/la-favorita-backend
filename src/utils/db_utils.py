from typing import Union

from flask import jsonify, Response
from flask_bcrypt import Bcrypt
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from pymongo.mongo_client import MongoClient

from config import DATABASE_URI


def db_connection() -> Union[Database, tuple[Response, int]]:
    try:
        client = MongoClient(DATABASE_URI)
        database = client["test_la_favorita"]
        return database
    except ConnectionFailure as e:
        return jsonify({"err": f"Error de conexión a la base de datos: {e}"}), 500


# Instancias necesarias para la conexión a la base de datos, el cifrado de contraseñas y autenticación JWT
db = db_connection()
bcrypt = Bcrypt()
