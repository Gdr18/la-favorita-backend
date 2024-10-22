from pymongo.mongo_client import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask import jsonify, Response
from typing import Union

from config import database_uri


def db_connection() -> Union[Database, tuple[Response, int]]:
    try:
        client = MongoClient(database_uri)
        database = client["test_la_favorita"]
        return database
    except ConnectionFailure as e:
        return jsonify({"err": f"Error de conexión a la base de datos: {e}"}), 500


# Instancias necesarias para la conexión a la base de datos, el cifrado de contraseñas y autenticación JWT
db = db_connection()
bcrypt = Bcrypt()
jwt = JWTManager()
